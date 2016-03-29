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

import json

import sqlalchemy as sa
from sqlalchemy import orm as sa_orm
from sqlalchemy.ext.declarative import declarative_base

from mlm import consts


BASE = declarative_base()


class Member(BASE):
    __tablename__ = "member"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.String(250), unique=True)
    active = sa.Column(sa.Boolean, default=True)
    leader_score = sa.Column(sa.Integer, default=0)

    def __repr__(self):
        return "<Member %(name)s [%(status)s]>" % {
            "name": self.name,
            "status": "Active" if self.active else "Inactive :("}


class Event(BASE):
    __tablename__ = "event"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    datetime = sa.Column(sa.DateTime, unique=True)
    type = sa.Column(sa.String(250))
    # TODO: make this field as json by default
    extra_field = sa.Column(sa.String(1000), default="{}")

    @property
    def time(self):
        return self.datetime.strftime("%H:%M")

    @property
    def weekday(self):
        return consts.WEEKDAYS[self.datetime.weekday()]

    @property
    def extradata(self):
        return json.loads(self.extra_field)

    def __str__(self):
        return "%s: %s at %s UTC" % (self.type.capitalize(),
                                    self.weekday,
                                    self.time)


class Election(BASE):
    __tablename__ = "election"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    datetime = sa.Column(sa.DateTime)
    lucky_man_name = sa.Column(sa.String(250), sa.ForeignKey('member.name'))
    lucky_man = sa_orm.relationship(Member)
    meeting_id = sa.Column(sa.Integer, sa.ForeignKey('event.id'))
    meeting = sa_orm.relationship(Event)

    @property
    def date(self):
        return "%s (%s) - %s" % (self.datetime.strftime("%d.%m.%y"),
                                 self.weekday,
                                 self.datetime.strftime("%H:%M UTC"))

    @property
    def weekday(self):
        return consts.WEEKDAYS[self.datetime.weekday()]

    def __repr__(self):
        return "<Election for meeting %s; leader: %s>" % (
            self.date, self.lucky_man.name)
