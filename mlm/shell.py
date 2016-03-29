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

"""
Command-line interface to MLM
"""

import inspect
import pkgutil
import sys

import argparse

import mlm
from mlm.app import api
from mlm import commands
from mlm.commands import utils


class Shell(object):

    def __init__(self, argv):
        self.args = self._get_base_parser().parse_args(argv)

    def _get_base_parser(self):
        parser = argparse.ArgumentParser(
            prog="mlm",
            description=__doc__.strip(),
            add_help=True
        )

        parser.add_argument('-v', '--version',
                            action='version',
                            version=mlm.__version__)

        self._append_subcommands(parser)

        return parser

    def _append_subcommands(self, parent_parser):
        subcommands = parent_parser.add_subparsers(help='<subcommands>')
        for importer, modname, _ in pkgutil.iter_modules(commands.__path__):
            # load all submodules
            importer.find_module(modname).load_module(modname)
        for group_cls in utils.BaseCommand.__subclasses__():
            group_parser = subcommands.add_parser(
                group_cls.__name__.lower(),
                help=group_cls.__doc__)
            subcommand_parser = group_parser.add_subparsers()

            for name, callback in inspect.getmembers(
                    group_cls(), predicate=inspect.ismethod):
                command = name.replace('_', '-')
                desc = callback.__doc__ or ''
                help_message = desc.strip().split('\n')[0]
                arguments = getattr(callback, 'args', [])

                command_parser = subcommand_parser.add_parser(
                    command, help=help_message, description=desc)
                for (args, kwargs) in arguments:
                    command_parser.add_argument(*args, **kwargs)
                command_parser.set_defaults(func=callback)

    def call_func(self):
        self.args.func(api.API(), self.args)


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    shell = Shell(args)
    shell.call_func()


if __name__ == "__main__":
    main()
