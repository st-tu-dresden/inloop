from typing import Any

from django.core.management.base import BaseCommand

from constance import config

from inloop.gitload.tasks import load_tasks_async


class Command(BaseCommand):
    help = "Synchronizes with the Git repository and loads the task into the system."

    def handle(self, *args: str, **options: Any) -> None:
        if config.GITLOAD_URL and config.GITLOAD_BRANCH:
            load_tasks_async()
            self.stdout.write("Job submitted.")
        else:
            self.stderr.write("GITLOAD_URL or GITLOAD_BRANCH not configured.")
