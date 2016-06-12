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
import re

import mlm
from mlm import config
from tests.unit import test


class ConfigSampleTestCase(test.TestCase):
    def test_sections_format(self):
        matcher = re.compile(r"^[a-zA-Z_0-9]*$")
        for section in config._OPTIONS:
            if matcher.match(section) is None:
                self.fail("Section '%s' has wrong format. Name of section "
                          "can include only letters, numbers and _ character."
                          % section)

    def test_options_format(self):
        for section, options in config._OPTIONS.items():
            for option, data in options.items():
                self.assertIn("defaults", data,
                              msg="Missed 'defaults' key in '%s' option dict "
                                  "of '%s' section" % (option, section))
                self.assertIn("type", data,
                              msg="Missed 'type' key in '%s' option dict "
                                  "of '%s' section" % (option, section))
                self.assertIn("description", data,
                              msg="Missed 'description' key in '%s' option "
                                  "dict of '%s' section" % (option, section))
                self.assertEqual(3, len(data),
                                 msg="'%s' option dict of '%s' section can "
                                     "include only 'defaults', 'type' and "
                                     "'description' keys." % (option, section))

    def test_sample_config_is_not_outdated(self):
        sample_file = os.path.join(
            os.path.dirname(os.path.dirname(mlm.__file__)),
            "samples",
            "mlm.ini")
        if not os.path.isfile(sample_file):
            self.fail("Sample config file is missed. Run `tox -egenconfig` to "
                      "create it.")
        with open(sample_file) as f:
            conf = "".join(f.readlines())
        conf = conf.rstrip("\n")
        sample = config.make_sample().rstrip("\n")
        self.assertEqual(sample, conf,
                         msg="Sample config file is ourdated. You need execute"
                             " `tox -egenconfig` to update it.")
