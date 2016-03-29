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

import re

from mlm.commands import utils
from mlm import consts


class Meeting(utils.BaseCommand):
    @utils.args("--weekday", type=str, metavar="<name>",
                help="The day of meeting. Should be one of: %s" %
                     ", ".join(consts.WEEKDAYS))
    @utils.args("--time", type=str, metavar="<time>",
                help="Time of meeting in UTC. Expected format: 'H:M'.")
    def add(self, api, args):
        """Add meeting."""
        if args.weekday not in consts.WEEKDAYS:
            raise ValueError("Wrong value of weekday.")
        if not re.match(r"^([0-9]|0[0-9]|1?[0-9]|2[0-3]):[0-5]?[0-9]$",
                        args.time):
            raise ValueError("Wrong format of time.")
        api.add_meeting(consts.WEEKDAYS.index(args.weekday), args.time)

    def list(self, api, args):
        """Show all meetings"""
        meetings = api.get_meetings()
        if meetings:
            print(utils.make_table([(m.weekday, m.time) for m in meetings],
                                   headers=["Weekday", "Time"],
                                   title="Available meetings"))
        else:
            print("There is no scheduled meetings.")
