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

import datetime
import multiprocessing
import random
import time
import threading
import smtplib

import flask
from jinja2 import Environment, FileSystemLoader
from flask import render_template


class Flask(object):
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


class Tasks(object):
    def __init__(self, api, config, should_stop):
        self.api = api
        self.config = config
        self.should_stop = should_stop

    def _render_html(self, template_dir, file_name, **kwargs):
        j2_env = Environment(loader=FileSystemLoader(template_dir),
                             trim_blocks=True)

        return j2_env.get_template(file_name).render(**kwargs)

    def send_email_notification(self, lucky_man, date):
        """Sends email notification to lucky man by email.

        :param lucky_man: mlm.db.models.Member object of current leader
        :param date: date of meeting
        """
        path, template = self.config.mail_notification.template.rsplit("/", 1)
        email_message = self._render_html(path, template,
                                          username=lucky_man.name,
                                          date=date)
        try:
            server = smtplib.SMTP(self.config.mail_notification.smtp_url)
            server.sendmail(self.config.mail_notification.email_from,
                            lucky_man.email, email_message)
            print("Successfully sent email")
        except smtplib.SMTPException:
            print("Error: unable to send email")

    def process_elections(self):
        while not self.should_stop.isSet():
            meeting, date = self.api.get_next_meeting()

            elections = self.api.get_all_elections()

            election = [e for e in elections
                        if e.datetime == date and e.meeting.id == meeting.id]

            print("Meeting: %s" % meeting)
            print("Date %s" % date)

            if not election:
                members = self.api.get_members(only_active=True)

                if elections:
                    # we should elect one person two times in a row
                    previous_leader = elections[-1].lucky_man
                    members = [m for m in members if m != previous_leader]

                choices = []
                for m in members:
                    weight = len(members) - m.leader_score % len(members)
                    # lets increase the difference between weights
                    weight *= 10
                    choices.append((m, weight))

                total = sum(w for c, w in choices)
                r = random.uniform(0, total)
                upto = 0
                lucky_man = None
                for c, w in choices:
                    if upto + w >= r:
                        lucky_man = c
                        break
                    upto += w
                print("New leader: %s" % lucky_man)
                t = threading.Thread(target=self.send_email_notification,
                                     args=(lucky_man, date))
                t.start()
                self.api.save_election(meeting, date, lucky_man)
            else:

                # sleep until next meeting starts or should_stop event isSet.
                while (datetime.datetime.utcnow() <
                        (date + datetime.timedelta(minutes=5)) and
                        not self.should_stop.isSet()):
                    time.sleep(1)

    def __call__(self):
        """worker process"""
        # TODO: add notification thread
        elections_t = threading.Thread(target=self.process_elections)
        elections_t.start()
        elections_t.join()


def start(api, config):
    should_stop = threading.Event()
    tasks_p = multiprocessing.Process(name="tasks", target=Tasks(api, config,
                                                                 should_stop))
    flask_p = multiprocessing.Process(name="flask",
                                      target=Flask(api, config))

    tasks_p.start()
    flask_p.start()
    while True:
        try:
            time.sleep(0.5)
        except KeyboardInterrupt:
            should_stop.set()


if __name__ == '__main__':
    pass
