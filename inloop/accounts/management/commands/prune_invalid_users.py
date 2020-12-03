from typing import Any

from django.core.management.base import BaseCommand

from inloop.accounts.models import prune_invalid_users


class Command(BaseCommand):
    help = "Delete accounts that haven't been activated in time."

    def handle(self, *args: str, **options: Any) -> None:
        num_deleted = prune_invalid_users()
        self.stdout.write(f"Pruned {num_deleted} invalid account(s).")
