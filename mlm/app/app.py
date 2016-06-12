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

import multiprocessing
import time
import threading

from mlm.app import rest
from mlm.app import tasks


def start(api, config):
    should_stop = threading.Event()
    tasks_p = multiprocessing.Process(
        name="tasks",
        target=tasks.Tasks(api, config, should_stop))
    flask_p = multiprocessing.Process(
        name="flask",
        target=rest.WebServer(api, config))

    tasks_p.start()
    flask_p.start()
    while True:
        try:
            time.sleep(0.5)
        except KeyboardInterrupt:
            should_stop.set()
