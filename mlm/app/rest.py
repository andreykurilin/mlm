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

        def get_cls_for_cell(i, n):
            """
            :param i: index of column
            :param n: number of columns
            """
            if i == 0:
                return "left_cell"
            elif i == n:
                return "right_cell"
            return "cell"

        # Make header
        for i in range(len(headers)):
            cls = "header_cell %s" % get_cls_for_cell(i, len(headers)-1)
            table.append("<div class='%s'>%s</div>" % (cls, headers[i]))

        for row in data:
            for i in range(len(headers)):
                key = headers[i]
                cls = get_cls_for_cell(i, len(headers)-1)
                key = key.lower()
                if key in formaters:
                    value = formaters[key](row)
                else:
                    value = getattr(row, key)
                table.append("<div class='%s'>%s</div>" % (cls, value))
        table.append("</div><br/>")
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
                                   "%y.%m.%d"),
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
