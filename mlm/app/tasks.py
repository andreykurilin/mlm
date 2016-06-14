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

import collections
import datetime
import random
import time
import threading
import smtplib

from jinja2 import Environment, FileSystemLoader


class Tasks(object):
    def __init__(self, api, config, should_stop):
        self.api = api
        self.config = config
        self.exit = should_stop
        self.election_queue = collections.deque()

    def _render_html(self, template_dir, file_name, **kwargs):
        j2_env = Environment(loader=FileSystemLoader(template_dir),
                             trim_blocks=True)

        return j2_env.get_template(file_name).render(**kwargs)

    def process_elections(self):
        while not self.exit.isSet():
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
                    members = [m for m in members
                               if m.id != previous_leader.id]

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

                election = self.api.save_election(meeting, date, lucky_man.id)
                self.election_queue.append(election)
            else:

                # sleep until next meeting starts or should_stop event isSet.
                while (datetime.datetime.utcnow() <
                        (date + datetime.timedelta(minutes=5)) and
                        not self.exit.isSet()):
                    time.sleep(1)

    def notifier(self):
        if not self.config.mail_notification.enabled:
            return

        email_from = self.config.mail_notification.email_from
        smtp_url = self.config.mail_notification.smtp_url
        path, template = self.config.mail_notification.template.rsplit("/", 1)
        username = self.config.mail_notification.login
        password = self.config.mail_notification.password

        while not self.exit.isSet():
            if not len(self.election_queue):
                time.sleep(1)
            else:
                election = self.election_queue.popleft()
                email_to = election.lucky_man.contacts["email"]

                email_message = self._render_html(
                    path, template,
                    username=election.lucky_man.name,
                    date=election.date,
                    email_from=email_from,
                    email_to=email_to
                )
                try:
                    server = smtplib.SMTP(smtp_url)
                    server.starttls()
                    server.login(username, password)

                    server.sendmail(email_from, email_to, email_message)
                    print("Successfully sent email")
                except smtplib.SMTPException as e:
                    raise e
                    print("Error: unable to send email")
                else:
                    server.quit()

    def __call__(self):
        """worker process"""
        elections_t = threading.Thread(target=self.process_elections)
        notification_t = threading.Thread(target=self.notifier)

        elections_t.start()
        notification_t.start()

        elections_t.join()
        notification_t.join()
