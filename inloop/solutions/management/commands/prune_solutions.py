from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from inloop.solutions.models import get_prunable_solutions
from inloop.tasks.models import Task


class Command(BaseCommand):
    help = 'Tidy up solutions to keep just the last max_keep solutions per user and task.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max_keep',
            help='Number of solutions to retain.',
            default=10,
            type=int
        )

    def handle(self, *args, **options):
        max_keep = options['max_keep']
        if max_keep < 1:
            raise CommandError('max_keep must be >= 1.')
        solutions_to_delete = get_prunable_solutions(
            users=User.objects.all(),
            tasks=Task.objects.all(),
            max_keep=max_keep,
        )
        num_deleted = 0
        for solutions in solutions_to_delete:
            num_deleted += solutions.count()
            solutions.delete()
        self.stdout.write(f'Pruned {num_deleted} solution(s).')
