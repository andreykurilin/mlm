import threading
import mock

from mlm.app.app import Tasks
from mlm.app.db_models import Member
from mlm import config
from tests.unit import test


class TasksTestCase(test.TestCase):
    def setUp(self):
        super(TasksTestCase, self).setUp()
        self.config = config.Config()
        should_stop = threading.Event()
        self.task = Tasks(None, self.config, should_stop)

    @mock.patch('mlm.app.app.FileSystemLoader.get_source')
    def test_render_template(self, get_source_mock):
        name = "Doe"
        date = "12/12/12"
        filename = "templates/email_template.html"
        get_source_mock.return_value = ("{{ username }} {{ date }}",
                                        filename, 9999)

        message = self.task._render_html("templates",
                                         "",
                                         username=name,
                                         date=date)
        self.assertIn(name, message)
        self.assertIn(date, message)

    @mock.patch('mlm.app.app.Tasks._render_html')
    @mock.patch('mlm.app.app.smtplib.SMTP.sendmail')
    def test_send_email_notification(self, send_mail_mock,
                                     render_template_mock):
        lucky_man = Member()
        lucky_man.name = "John Doe"
        lucky_man.email = "jdoe@gmail.com"
        date = "12/12/12"
        message = "Hello, world!!!"
        render_template_mock.return_value = message

        self.task.send_email_notification(lucky_man, date)

        send_mail_mock.assert_called_with(
            self.config.mail_notification.email_from, lucky_man.email,
            message)
