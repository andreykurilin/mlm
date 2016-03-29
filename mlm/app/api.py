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
from mlm import consts


class API(object):

    home_dir = os.path.expanduser("~/.mlm")

    def __init__(self):
        self.__db_session = None
        if not os.path.exists(self.home_dir):
            os.mkdir(self.home_dir)
        if not os.path.exists(self.db_file):
            self.init_db()

    @property
    def db_file(self):
        return "sqlite:///%s/db.sql" % self.home_dir

    @property
    def _db_session(self):
        if not self.__db_session:
            _engine = sa.create_engine(self.db_file)
            db_models.BASE.metadata.bind = _engine
            session_maker = sa_orm.sessionmaker(bind=_engine)
            self.__db_session = session_maker()
        return self.__db_session

    def init_db(self):
        db_models.BASE.metadata.create_all(self._db_session.bind)

    def add_member(self, name):
        """Add new member to team."""
        self._db_session.add(db_models.Member(name=name))
        self._db_session.commit()

    def get_member(self, member_id):
        """Obtain member by ID."""
        member = self._db_session.query(db_models.Member).filter_by(
            id=member_id).first()
        if not member:
            raise Exception("There is no member with id '%s'." % member_id)
        return member

    def get_members(self, only_active=False):
        """Obtain all members."""
        if only_active:
            return self._db_session.query(db_models.Member).filter_by(
                    active=True).all()
        return self._db_session.query(db_models.Member).all()

    def deactivate_member(self, member_id):
        member = self.get_member(member_id)
        if not member.active:
            raise Exception("%s (id=%s) is already inactive" % (member.name,
                                                                member.id))
        member.active = False
        self._db_session.commit()
        return member

    def add_meeting(self, weekday, time):
        date = consts.get_first_monday()
        if weekday > 0:
            date = date + dt.timedelta(days=weekday)

        time = dt.datetime.strptime(time, "%H:%M")
        date = date.replace(hour=time.hour, minute=time.minute)

        meeting = db_models.Event(type="meeting", datetime=date)
        try:
            self._db_session.add(meeting)
            self._db_session.commit()
        except exc.IntegrityError:
            raise ValueError("%s is already exist." % meeting)

    def get_meetings(self):
        meetings = self._db_session.query(db_models.Event).filter_by(
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
        return self._db_session.query(db_models.Election).all()

    def get_last_election(self):
        return self._db_session.query(db_models.Election).order_by(
                db_models.Election.id.desc()).first()

    def save_election(self, meeting, date, lucky_man):
        lucky_man.leader_score += 1
        self._db_session.add(db_models.Election(datetime=date,
                                                lucky_man=lucky_man,
                                                meeting=meeting))
        self._db_session.commit()

    def start_app(self, port, name):
        app.start(self, port, name)
