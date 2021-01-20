from pathlib import Path
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError, CommandParser

from inloop.grading.copypasta import jplag_check
from inloop.tasks.models import Task

User = get_user_model()


class Command(BaseCommand):
    help = "Perform a plagiarism check on each user's last submission for a task category."

    def add_arguments(self, parser: CommandParser) -> None:
        default_similarity = settings.JPLAG_DEFAULT_SIMILARITY
        parser.add_argument("category_name", help="Name of the task category to check")
        parser.add_argument("result_dir", help="Path where JPlag results should be saved to")
        parser.add_argument(
            "--min_similarity",
            help=f"Minimum similarity (percent, default: {default_similarity})",
            type=int,
            default=default_similarity,
        )

    def handle(self, *args: str, **options: Any) -> None:
        users = User.objects.filter(is_staff=False)
        tasks = Task.objects.filter(category__name=options["category_name"])
        result_dir = Path(options["result_dir"])
        if result_dir.exists():
            raise CommandError("result_dir already exists")
        jplag_check(users, tasks, options["min_similarity"], result_dir)
