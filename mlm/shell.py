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
from mlm import api
from mlm import commands
from mlm.commands import utils


def main(input_args=None):
    if input_args is None:
        input_args = sys.argv[1:]

    # base parser
    parser = argparse.ArgumentParser(
        prog="mlm",
        description=__doc__.strip(),
        add_help=True
    )

    parser.add_argument('-v', '--version',
                        action='version',
                        version=mlm.__version__)

    parser.add_argument('--config-file', type=str, metavar="<file>",
                        help="Path to configuration file.")

    # all subcommands
    subcommands = parser.add_subparsers(help='<subcommands>')
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

    # parse and run
    args = parser.parse_args(input_args)
    args.func(api.API(args.config_file), args)


if __name__ == "__main__":
    main()
