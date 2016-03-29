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


class Members(utils.BaseCommand):
    @utils.args("name", type=str, metavar="<name>",
                help="The name of new member.")
    def add(self, api, args):
        """Add new member."""
        api.add_member(args.name)
        print("'%s' is successfully added to team. Congrats!" % args.name)

    def list(self, api, args):
        """Show all members"""
        active_members = []
        inactive_members = []
        for member in api.get_members():
            if member.active:
                active_members.append(member)
            else:
                inactive_members.append(member)
        headers = ["ID", "Name", "Score"]
        print(utils.make_table([(m.id, m.name, m.leader_score)
                                for m in active_members],
                               headers=headers,
                               title="Current team"))
        if inactive_members:
            print(utils.make_table([(m.id, m.name, m.leader_score)
                                    for m in inactive_members],
                                   headers=headers,
                                   title="Ex-members :("))

    @utils.args("id", type=int, metavar="<id>", help="The ID of a member.")
    def delete(self, api, args):
        """Delete a member from the team:("""
        member = api.deactivate_member(args.id)
        print("%s (id=%s) is set as inactive." % (member.name, member.id))
