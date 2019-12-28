import random
from datetime import datetime, timedelta
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.transaction import atomic
from django.utils.timezone import make_aware

from inloop.solutions.models import Solution
from inloop.tasks.models import Task

User = get_user_model()

file_dir = Path(__file__).resolve().parent


class Command(BaseCommand):
    help = 'Generate submissions for demo purposes.'

    dateformat = '%d.%m.%Y'
    help_text_safe_dateformat = 'dd.mm.YYYY'

    def create_users(self, number):
        users = []
        for i in range(number):
            username = f'GeneratedUser{i}'
            email = f'generated-user-{i}@example.com'
            password = 'secret'
            user, _ = User.objects.get_or_create(
                username=username, email=email, password=password
            )
            users.append(user)
        return users

    def create_solution(self, user, task, start_date, end_date):
        passed = random.choice([True, False])
        seconds_until_end_date = int((end_date - start_date).total_seconds())
        submission_date = start_date + timedelta(
            seconds=random.randint(0, seconds_until_end_date)
        )
        solution = Solution.objects.create(
            author=user, task=task, passed=passed,
        )
        # Because of auto_now_add, we can't set a custom
        # submission_date through the constructor
        solution.submission_date = submission_date
        solution.save()
        return solution

    def add_arguments(self, parser):
        parser.add_argument(
            '--start_date',
            help=f'Start date (Format: {self.help_text_safe_dateformat})',
            default=(datetime.now() - timedelta(days=365)).strftime(self.dateformat),
        )
        parser.add_argument(
            '--end_date',
            help=f'End date (Format: {self.help_text_safe_dateformat})',
            default=datetime.now().strftime(self.dateformat),
        )
        parser.add_argument(
            '--solutions_number',
            help='Number of solutions to generate',
            type=int,
            default=1000
        )
        parser.add_argument(
            '--users_number',
            help='Number of users to generate',
            type=int,
            default=10
        )
        parser.add_argument(
            '--force',
            help='Immediately perform submission creation without prompt',
            default=False
        )

    def handle(self, *args, **options):
        start_date = make_aware(datetime.strptime(options['start_date'], self.dateformat))
        end_date = make_aware(datetime.strptime(options['end_date'], self.dateformat))
        solutions_number = options['solutions_number']
        users_number = options['users_number']
        verbosity = options['verbosity']
        force = options['force']
        if start_date > end_date:
            raise ValueError('Start date should be before end date.')
        if not Task.objects.exists():
            raise ValueError('There are no tasks available.')
        if not force:
            if input('This will create user accounts and solutions. Continue? (y/n)') != 'y':
                return
        with atomic():
            users = self.create_users(users_number)
            tasks = Task.objects.all()
            all_solutions = []
            for _ in range(solutions_number):
                user = random.choice(users)
                task = random.choice(tasks)
                all_solutions.append(self.create_solution(
                    user, task, start_date, end_date
                ))
        if verbosity > 0:
            self.stdout.write(f'Successfully created {len(users)} users.')
            self.stdout.write(f'Successfully created {len(all_solutions)} solutions.')
