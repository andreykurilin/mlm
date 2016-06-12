# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import datetime as dt
import os

import sqlalchemy as sa
from sqlalchemy import exc
from sqlalchemy import orm as sa_orm

from mlm.app import app
from mlm.app import db_models
from mlm import config
from mlm import consts


class API(object):

    def __init__(self, config_file):
        self._config = config.Config(config_file)
        self.__db_session = None

        if not os.path.exists(config.HOME_DIR):
            os.mkdir(config.HOME_DIR)

        self._db_engine = sa.create_engine(
            self._config.db.sqlite_connection_string)
        # db_models.BASE.metadata.bind = self._db_engine
        self._session_factory = sa_orm.sessionmaker(bind=self._db_engine,
                                                    expire_on_commit=False,
                                                    autocommit=True)

        if not os.path.exists(self._config.db.sqlite_connection_string):
            self.init_db()

    def get_db_session(self):
        return self._session_factory()

    def db_query(self, model, session=None):
        session = session or self.get_db_session()
        return session.query(model)

    def init_db(self):
        db_models.BASE.metadata.create_all(self.get_db_session().bind)

    def add_member(self, name):
        """Add new member to team."""
        self.get_db_session().add(db_models.Member(name=name))

    def get_member(self, member_id, session=None):
        """Obtain member by ID."""
        session = session or self.get_db_session()
        member = self.db_query(db_models.Member, session).filter_by(
            id=member_id).first()
        if not member:
            raise Exception("There is no member with id '%s'." % member_id)
        return member

    def get_members(self, only_active=False):
        """Obtain all members."""
        if only_active:
            return self.db_query(db_models.Member).filter_by(active=True).all()
        return self.db_query(db_models.Member).all()

    def deactivate_member(self, member_id):
        session = self.get_db_session()
        with session.begin():
            member = self.get_member(member_id)
            if not member.active:
                raise Exception("%(name)s (id=%(id)s) is already inactive" % {
                    "name": member.name, "id": member.id})
            member.active = False
        return member

    def add_meeting(self, weekday, time):
        date = consts.get_first_monday()
        if weekday > 0:
            date = date + dt.timedelta(days=weekday)

        time = dt.datetime.strptime(time, "%H:%M")
        date = date.replace(hour=time.hour, minute=time.minute)

        meeting = db_models.Event(type="meeting", datetime=date)
        try:
            self.get_db_session().add(meeting)
        except exc.IntegrityError:
            raise ValueError("%s is already exist." % meeting)

    def get_meetings(self):
        meetings = self.db_query(db_models.Event).filter_by(
                type="meeting").all()
        return sorted(meetings, key=lambda m: m.datetime)

    def get_next_meeting(self):
        now = dt.datetime.utcnow()
        current_day = now.weekday()

        meetings = self.get_meetings()

        # if there is no meetings after current utcnow(), use first meeting of
        # the week as a next one.
        next_meeting = meetings[0]

        for meeting in meetings:
            if meeting.datetime.weekday() == current_day:
                if now.time() < meeting.datetime.time():
                    next_meeting = meeting
                    break
            elif current_day < meeting.datetime.weekday():
                next_meeting = meeting
                break

        # find the date of next meeting
        date = now + dt.timedelta(
                days=(7 - current_day + next_meeting.datetime.weekday()) % 7)
        date = date.replace(hour=next_meeting.datetime.hour,
                            minute=next_meeting.datetime.minute,
                            second=0, microsecond=0)

        return next_meeting, date

    def get_all_elections(self):
        return self.db_query(db_models.Election).all()

    def get_last_election(self):
        return self.db_query(db_models.Election).order_by(
                db_models.Election.id.desc()).first()

    def save_election(self, meeting, date, member_id):
        session = self.get_db_session()
        with session.begin():
            member = self.get_member(member_id, session=session)
            session.add(db_models.Election(datetime=date,
                                           lucky_man=member,
                                           meeting=meeting))
            member.leader_score += 1

    def start_app(self):
        app.start(self, self._config)
