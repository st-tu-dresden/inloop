import json
import logging
from glob import glob
from os.path import basename, dirname, join
from subprocess import CalledProcessError, check_call

from django.conf import settings
from django.db.transaction import atomic

from huey.contrib.djhuey import db_task

from inloop.gh_import.git import GitRepository
from inloop.tasks.models import Task

logger = logging.getLogger(__name__)

NEWS_FILE = "news.md"
META_FILE = "meta.json"
TASK_FILE = "task.md"


@db_task()
def update_tasks():
    # git refresh
    git_root = settings.GIT_ROOT
    if not settings.DEBUG:
        logger.info("Pulling changes from git")
        repo = GitRepository(git_root)
        repo.pull()

    # find task directories
    meta_files = glob(join(git_root, '*', META_FILE))
    task_dirs = [dirname(f) for f in meta_files]
    logger.info("found %d task directories", len(task_dirs))
    for task_dir in task_dirs:
        process_dir(task_dir)

    # ZIP the tests
    logger.info("zipping the unit tests w/ gradle")
    gradlew_exe = join(git_root, 'gradlew')
    try:
        check_call([gradlew_exe, '-q', 'zipTests'], cwd=git_root)
    except CalledProcessError as e:
        logger.error("gradlew FAILED, exception follows.")
        logger.exception(e)


def process_dir(task_dir):
    """Processes a single task directory."""
    task_name = basename(task_dir)
    logger.info("Processing task %s", task_name)
    try:
        with atomic():
            data = {}
            with open(join(task_dir, META_FILE), encoding="utf-8") as json_file:
                data.update(json.load(json_file))
            with open(join(task_dir, TASK_FILE), encoding="utf-8") as markdown_file:
                data["description"] = markdown_file.read()
            Task.objects.update_or_create_related(system_name=task_name, data=data)
        logger.info("Successfully imported %s", task_name)
    except Exception as e:
        logger.error("Importing task %s FAILED, exception follows.", task_name)
        logger.exception(e)
