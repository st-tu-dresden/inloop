from subprocess import check_call

from django.conf import settings
from django.dispatch import receiver

from inloop.gitload.signals import repository_loaded
from inloop.solutions.signals import solution_submitted
from inloop.testrunner.models import check_solution_async


@receiver(repository_loaded, dispatch_uid='testrunner_repository_loaded')
def handle_repository_loaded(sender, repository, **kwargs):
    """
    Listen for the repository_loaded signal and (re-) build the docker image.
    """
    args = ['docker', 'build', '--pull', '-t', settings.TESTRUNNER_IMAGE, '.']
    check_call(args, cwd=str(repository.path), timeout=60)


@receiver(solution_submitted, dispatch_uid='testrunner_solution_submitted')
def handle_solution_submitted(sender, solution, **kwargs):
    """Receiver for the solution_submitted signal in inloop.solutions."""
    check_solution_async(solution.id)
