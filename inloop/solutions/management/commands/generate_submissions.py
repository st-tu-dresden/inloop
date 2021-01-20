import functools
import random
from datetime import datetime, timedelta
from typing import Any, Sequence

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db.transaction import atomic
from django.utils import timezone

from inloop.solutions.models import Solution
from inloop.tasks.models import Task


class Command(BaseCommand):
    help = "Generate submissions for demo purposes."

    MAX_USERS = 10 ** 4
    AVG_SOLUTIONS_PER_HOUR = 0.5

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--success_rate",
            help="Ratio of solutions to mark as passed (e.g., 0.25)",
            default=0.25,
            type=float,
        )
        parser.add_argument("num_users", help="Number of users to generate", type=int)
        parser.add_argument("num_solutions", help="Number of solutions to generate", type=int)

    def handle(self, *args: str, **options: Any) -> None:
        success_rate = options["success_rate"]
        num_solutions = options["num_solutions"]
        num_users = options["num_users"]
        if not settings.DEBUG:
            raise CommandError("This command should only be used in DEBUG mode.")
        if num_users < 1 or num_solutions < 1:
            raise CommandError("num_users and num_solutions must be >= 1.")
        if num_users > self.MAX_USERS:
            raise CommandError(f"num_users must be <= {self.MAX_USERS}.")
        if not (0.0 <= success_rate <= 1.0):
            raise CommandError("success_rate must be within range [0.0, 1.0].")
        with atomic():
            self.generate_submissions(num_users, num_solutions, success_rate)
        self.stdout.write(f"Successfully created {num_users} user(s).")
        self.stdout.write(f"Successfully created {num_solutions} solution(s).")

    def generate_submissions(
        self, num_users: int, num_solutions: int, success_rate: float
    ) -> None:
        if Solution.objects.exists():
            raise CommandError("The solutions table must be empty.")
        tasks = Task.objects.all()
        if not tasks:
            raise CommandError("There are no tasks available.")
        now = timezone.now()
        start_date = now.replace(year=2015, month=4, day=15)  # birthday of INLOOP (see #14)
        users = self.generate_users(num_users, date_joined=start_date)
        for _ in range(num_solutions):
            if start_date > now:
                raise CommandError("Too many solutions requested.")
            solution = Solution.objects.create(
                author=random.choice(users),
                task=random.choice(tasks),
                passed=(random.random() < success_rate),
            )
            # because of auto_now_add, we can't set a custom
            # submission_date through the constructor
            solution.submission_date = start_date
            solution.save()
            seconds_to_add = random.randint(0, int(2 * 3600 / self.AVG_SOLUTIONS_PER_HOUR))
            start_date += timedelta(seconds=seconds_to_add)

    def generate_users(self, num_users: int, *, date_joined: datetime) -> Sequence[User]:
        usernames = [f"student{n:04d}" for n in random.sample(range(self.MAX_USERS), num_users)]
        create_user = functools.partial(
            get_user_model().objects.get_or_create, date_joined=date_joined, password="secret"
        )
        return [
            create_user(username=username, email=f"{username}@localhost")[0]
            for username in usernames
        ]
