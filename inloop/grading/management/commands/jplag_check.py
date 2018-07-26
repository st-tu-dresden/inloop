from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from inloop.grading.copypasta import jplag_check
from inloop.tasks.models import Task

User = get_user_model()


class Command(BaseCommand):
    help = "Perform a plagiarism check on each user's last submission for a task category."

    def add_arguments(self, parser):
        parser.add_argument("category_name", help="Name of the task category to check")
        parser.add_argument("result_dir", help="Path where JPlag results should be saved to")
        parser.add_argument("--similarity", help="JPlag similarity", type=int, default=70)

    def handle(self, *args, **options):
        users = User.objects.filter(is_staff=False)
        tasks = Task.objects.filter(category__name=options["category_name"])
        if Path(options["result_dir"]).exists():
            raise CommandError("result_dir already exists")
        jplag_check(users, tasks, options["similarity"], options["result_dir"])
