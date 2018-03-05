from django.conf import settings

from constance import config
from huey.contrib.djhuey import db_task

from inloop.gitload.loader import load_tasks
from inloop.gitload.repo import GitRepository


@db_task()
def load_tasks_async():
    load_tasks(GitRepository(settings.REPOSITORY_ROOT, config.GITLOAD_URL, config.GITLOAD_BRANCH))
