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
import sys
import textwrap

from six.moves import configparser


HOME_DIR = os.path.expanduser("~/.mlm")

_OPTIONS = {
    "app": {
        "name": {
            "defaults": "Meeting Leader Manager",
            "type": str,
            "description": "Name of the app"
        },
        "port": {
            "defaults": 5000,
            "type": int,
            "description": "The port of the webserver."
        },
    },
    "db": {
        "sqlite_connection_string": {
            "defaults": "sqlite:///%s/db.sql" % HOME_DIR,
            "type": str,
            "description": "MLM uses sqlite to store all data. You can specify"
                           " non default place to store sqlite file via this "
                           "variable"
        }
    },
    "mail_notification": {
        "enabled": {
            "defaults": False,
            "type": bool,
            "description": "Enable or disable mail notification."
        },
        "email_from": {
            "defaults": "example@example.com",
            "type": str,
            "description": "E-mail address to send notification from."
        },
        "smtp_url": {
            "defaults": "smtp.gmail.com:587",
            "type": str,
            "description": "SMTP server."
        },
        "template": {
            "defaults": "templates/email_template.html",
            "type": str,
            "description": "Template for notification mail."
        },
    }
}


class _Section(object):
    def __init__(self, name, config_obj):
        self._name = name
        self._config = config_obj
        self._options = {}

    def _get_new_option(self, option):
        if option not in _OPTIONS[self._name]:
            raise AttributeError("There is no '%s' option in '%s' section of "
                                 "MLM config" % (option, self._name))
        if self._config.has_section(self._name):
            try:
                # TODO(andreykurilin): decode value by its type from _OPTIONS
                return self._config.get(self._name, option)
            except configparser.NoOptionError:
                pass

        return _OPTIONS[self._name][option]["defaults"]

    def __getattr__(self, option):
        if option not in self._options:
            self._options[option] = self._get_new_option(option)
        return self._options[option]

    def __repr__(self):
        return "<Section '%s'>" % self._name


class Config(object):
    """Wrapper for ConfigParser.ConfigParser"""

    DEFAULT_CONFIG_PATH = os.path.join(HOME_DIR, "mlm.ini")

    def __init__(self, config_file=None):
        self._config = configparser.ConfigParser()
        self._sections = {}

        if config_file is None:
            config_file = self.DEFAULT_CONFIG_PATH
        if os.path.isfile(config_file):
            self._config.read(config_file)

    def __getattr__(self, section):
        if section in _OPTIONS:
            if section not in self._sections:
                self._sections[section] = _Section(section, self._config)
            return self._sections[section]

        raise AttributeError("There is no section '%s' in MLM config" %
                             section)


def make_sample():
    config = []
    for section, options in sorted(_OPTIONS.items()):
        config.append("[%s]" % section)
        for option, data in sorted(options.items()):
            config.extend(textwrap.wrap(data["description"], 79,
                                        initial_indent="# ",
                                        subsequent_indent="# "))
            config.append("# Type: %s" % data["type"].__name__)
            config.append("#%s = %s" % (option, data["defaults"]))
            config.append("\n")
    return "\n".join(config)


if __name__ == '__main__':
    if len(sys.argv) not in (1, 2):
        raise Exception("Wrong usage of config generator.\nUsage:"
                        "python mlm/config.py [filename]")
    sample = make_sample()
    if len(sys.argv) == 2:
        with open(sys.argv[1], "w") as f:
            f.write(sample)
    else:
        print(sample)
