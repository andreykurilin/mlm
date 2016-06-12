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

import mock

from mlm.app import tasks
from mlm import config
from mlm.db import models
from tests.unit import test


class TasksTestCase(test.TestCase):
    def setUp(self):
        super(TasksTestCase, self).setUp()
        self.config = config.Config()

    @mock.patch('mlm.app.tasks.FileSystemLoader.get_source')
    def test_render_template(self, get_source_mock):
        task = tasks.Tasks(None, self.config, None)

        name = "Doe"
        date = "12/12/12"
        filename = "templates/email_template.html"
        get_source_mock.return_value = ("{{ username }} {{ date }}",
                                        filename, 9999)

        message = task._render_html("templates", "", username=name, date=date)
        self.assertIn(name, message)
        self.assertIn(date, message)

    @mock.patch('mlm.app.tasks.Tasks._render_html')
    @mock.patch('mlm.app.tasks.smtplib.SMTP.sendmail')
    def test_send_email_notification(self, send_mail_mock,
                                     render_template_mock):
        self.config.mail_notification._options["enabled"] = True
        lucky_man = models.Member(name="John Doe", email="jdoe@gmail.com")
        date = datetime.datetime.now()
        election = models.Election(datetime=date,
                                   lucky_man=lucky_man,
                                   meeting=None)

        message = "Hello, world!!!"

        event = mock.MagicMock()
        event.isSet.side_effect = False, True

        task = tasks.Tasks(None, self.config, event)
        task.election_queue.append(election)

        render_template_mock.return_value = message

        task.notifier()

        send_mail_mock.assert_called_with(
            self.config.mail_notification.email_from, lucky_man.email,
            message)
