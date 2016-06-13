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

import os

import sqlalchemy as sa
from sqlalchemy import exc
from sqlalchemy import orm as sa_orm

from mlm.db import models


class DBAPI(object):
    def __init__(self, config):
        self._cfg = config
        self.connection_str = "sqlite:///%s" % os.path.expanduser(
            self._cfg.db.sqlite_file)

        self._db_session = None
        _db_engine = sa.create_engine(self.connection_str)
        # db_models.BASE.metadata.bind = _db_engine
        self._session_factory = sa_orm.sessionmaker(bind=_db_engine,
                                                    expire_on_commit=False,
                                                    autocommit=True)

        if not os.path.exists(self.connection_str):
            self.init_db()

    def init_db(self):
        models.BASE.metadata.create_all(self.get_session().bind)

    def get_session(self):
        return self._session_factory()

    def query(self, model, session=None):
        session = session or self.get_session()
        return session.query(model)

    def add_member(self, name):
        """Add new member to team."""
        self.get_session().add(models.Member(name=name))

    def _get_member(self, member_id, session=None):
        """Obtain member by ID."""
        session = session or self.get_session()
        member = self.query(models.Member, session).filter_by(
            id=member_id).first()
        if not member:
            raise Exception("There is no member with id '%s'." % member_id)
        return member

    def get_member(self, member_id):
        return self._get_member(member_id)

    def get_members(self, only_active=False):
        """Obtain all members."""
        if only_active:
            return self.query(models.Member).filter_by(active=True).all()
        return self.query(models.Member).all()

    def deactivate_member(self, member_id):
        session = self.get_session()
        with session.begin():
            member = self._get_member(member_id, session)
            if not member.active:
                raise Exception(
                    "%(name)s (id=%(id)s) is already inactive" % {
                        "name": member.name, "id": member.id})
            member.active = False
        return member

    def add_meeting(self, date):
        meeting = models.Event(type="meeting", datetime=date)
        try:
            self.get_session().add(meeting)
        except exc.IntegrityError:
            raise ValueError("%s is already exist." % meeting)

    def get_meetings(self):
        return self.query(models.Event).filter_by(
            type="meeting").all()

    def get_elections(self):
        return self.query(models.Election).all()

    def get_last_election(self):
        return self.query(models.Election).order_by(
            models.Election.id.desc()).first()

    def save_election(self, meeting, date, member_id):
        session = self.get_session()
        with session.begin():
            member = self._get_member(member_id, session=session)
            election = models.Election(datetime=date,
                                       lucky_man=member,
                                       meeting=meeting)
            session.add(election)
            member.leader_score += 1
        return election
