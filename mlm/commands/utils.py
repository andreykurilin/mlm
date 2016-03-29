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

from tabulate import tabulate


class BaseCommand(object):
    """Base class for all commands"""
    pass


def args(*args, **kwargs):
    def _decorator(func):
        func.__dict__.setdefault("args", []).insert(0, (args, kwargs))
        return func
    return _decorator


def make_table(data, headers=(), title=None):
    table = tabulate(data, headers=headers)
    if title:
        table = "\n    ".join(("%s\n\n%s" % (title, table)).split("\n"))
    return "%s\n" % table
