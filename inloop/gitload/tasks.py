from django.conf import settings

from constance import config
from huey.contrib.djhuey import HUEY, db_task

from inloop.gitload.loader import load_tasks
from inloop.gitload.repo import GitRepository


@db_task()
def load_tasks_async():
    with HUEY.lock_task("import-lock"):
        load_tasks(GitRepository(
            settings.REPOSITORY_ROOT,
            config.GITLOAD_URL,
            config.GITLOAD_BRANCH
        ))
