from subprocess import check_call

from django.conf import settings
from django.dispatch import receiver

from inloop.gitload.signals import repository_loaded


@receiver(repository_loaded, dispatch_uid="testrunner_repository_loaded")
def handle_repository_loaded(sender, repository, **kwargs):
    """
    Listen for the repository_loaded signal and (re-) build the docker image.
    """
    args = ["docker", "build", "--pull", "-t", settings.DOCKER_IMAGE, "."]
    check_call(args, cwd=str(repository.path), timeout=60)
