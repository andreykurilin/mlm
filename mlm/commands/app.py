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

from mlm.commands import utils


class App(utils.BaseCommand):
    @utils.args("--name", type=str, metavar="<name>",
                default='Meeting Leader Manager',
                help="Name of the app. Defaults to 'Meeting Leader Manager'")
    @utils.args("--port", type=int, metavar="<port>", default=5000,
                help="The port of the webserver. Defaults to 5000")
    def start(self, api, args):
        """Add new member."""
        api.start_app(args.port, args.name)
