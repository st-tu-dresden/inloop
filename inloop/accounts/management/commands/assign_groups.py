from typing import Any, Iterable, Sequence

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandParser

from inloop.accounts.models import assign_to_groups


class Command(BaseCommand):
    help = "Randomly assign the given groups to users that do not already have a group."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "groups",
            nargs="+",
            metavar="GROUP",
            help="The names of the groups to assign users to.",
            type=str,
        )

    def handle(self, *args: str, **options: Any) -> None:
        groups = self.get_groups(options["groups"])
        num_users = assign_to_groups(users=User.objects.all(), groups=groups)
        self.stdout.write(f"Distributed {num_users} users to {len(groups)} groups.")

    def get_groups(self, group_names: Iterable[str]) -> Sequence[Group]:
        groups = []
        for name in group_names:
            group, _ = Group.objects.get_or_create(name=name)
            groups.append(group)
        return groups
