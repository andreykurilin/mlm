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

import flask
from flask import render_template


class WebServer(object):
    def __init__(self, api, config):
        self.api = api
        self.config = config
        self._cache = {}

    def _make_table(self, data, headers, formaters=None):
        table = ["<div class='table'>"]

        for i in range(0, len(headers)):
            if i == 0:
                column_cls = "left_cell"
            elif i == len(headers) - 1:
                column_cls = "right_cell"
            else:
                column_cls = "central_cell"
            table.append("\t<div class='%s'>" % column_cls)

            header = headers[i]

            table.append("\t\t<div class='header_cell cell'>%s</div>" % header)
            table.append("\t\t<hr style='border-top:1px dashed #000; "
                         "color: white;' />")
            for raw in data:
                key = header.lower()
                if key in formaters:
                    value = formaters[key](raw)
                else:
                    value = getattr(raw, key)
                table.append("\t\t<div class='cell'>%s</div>" % value)
            table.append("\t</div>")

        table.append("</div>")

        return "\n".join(table)

    def last_election(self):
        return "%s" % str(self.api.get_last_election())[1:-1]

    def index(self):
        election = self.api.get_last_election()
        if election:
            if election in self._cache:
                return self._cache[election]
            else:
                scores = self._make_table(
                    sorted(self.api.get_members(only_active=True),
                           key=lambda o: o.leader_score,
                           reverse=True),
                    headers=["Name", "Score"],
                    formaters={"score": lambda o: o.leader_score})

                elections = self.api.get_all_elections()
                elections.reverse()
                history = self._make_table(
                    elections,
                    headers=["Date", "Time", "Weekday", "Leader"],
                    formaters={"leader": lambda o: o.lucky_man.name,
                               "date": lambda o: o.datetime.strftime(
                                   "%d.%m.%y"),
                               "time":
                                   lambda o: "%s UTC" %
                                             o.datetime.strftime("%H:%M")})

                return render_template("index.html",
                                       title=self.config.app.name,
                                       date=election.date,
                                       name=election.lucky_man.name,
                                       scores=scores,
                                       history=history)
        else:
            return render_template("default.html")

    def __call__(self):
        """process worker"""
        f = flask.Flask(__name__,
                        template_folder='templates',
                        static_folder='static')

        f.add_url_rule("/last_election", None, self.last_election)
        f.add_url_rule("/", None,  self.index)

        f.run(host='0.0.0.0', port=self.config.app.port, threaded=True)
