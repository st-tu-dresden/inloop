from subprocess import check_call
from typing import Any, Type

from django.conf import settings
from django.dispatch import receiver

from inloop.gitload.repo import Repository
from inloop.gitload.signals import repository_loaded
from inloop.solutions.models import Solution
from inloop.solutions.signals import solution_submitted
from inloop.testrunner.models import check_solution_async


@receiver(repository_loaded, dispatch_uid="testrunner_repository_loaded")
def handle_repository_loaded(sender: Type[Any], repository: Repository, **kwargs: Any) -> None:
    """
    Listen for the repository_loaded signal and (re-) build the docker image.
    """
    image_name = settings.TESTRUNNER_OPTIONS["image"]
    args = ["docker", "build", "-t", image_name, "."]
    check_call(args, cwd=repository.path, timeout=60)


@receiver(solution_submitted, dispatch_uid="testrunner_solution_submitted")
def handle_solution_submitted(sender: Type[Any], solution: Solution, **kwargs: Any) -> None:
    """Receiver for the solution_submitted signal in inloop.solutions."""
    check_solution_async(solution.id)
