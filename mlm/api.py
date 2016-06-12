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

from mlm.app import app
from mlm import config
from mlm import consts
from mlm.db import api as dbapi


class API(object):

    def __init__(self, config_file):
        self._config = config.Config(config_file)
        self._db_api = dbapi.DBAPI(self._config)

    def add_member(self, name):
        """Add new member to team."""
        self._db_api.add_member(name)

    def get_member(self, member_id):
        """Obtain member by ID."""
        return self._db_api.get_member(member_id)

    def get_members(self, only_active=False):
        """Obtain all members."""
        return self._db_api.get_members(only_active)

    def deactivate_member(self, member_id):
        return self._db_api.deactivate_member(member_id)

    def add_meeting(self, weekday, time):
        date = consts.get_first_monday()
        if weekday > 0:
            date = date + dt.timedelta(days=weekday)

        time = dt.datetime.strptime(time, "%H:%M")
        date = date.replace(hour=time.hour, minute=time.minute)

        self._db_api.add_meeting(date)

    def get_meetings(self):
        return sorted(self._db_api.get_meetings(), key=lambda m: m.datetime)

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
        return self._db_api.get_elections()

    def get_last_election(self):
        return self._db_api.get_last_election()

    def save_election(self, meeting, date, member_id):
        return self._db_api.save_election(meeting, date, member_id)

    def start_app(self):
        app.start(self, self._config)
