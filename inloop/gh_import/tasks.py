import json
import logging
from glob import glob
from subprocess import check_call, CalledProcessError
from os.path import basename, dirname, join

from django.conf import settings
from django.db.transaction import atomic
from huey.djhuey import task

from inloop.gh_import.git import GitRepository
from inloop.tasks.models import Task

logger = logging.getLogger(__name__)

NEWS_FILE = "news.md"
META_FILE = "meta.json"
TASK_FILE = "task.md"


@task()
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
            with open(join(task_dir, META_FILE)) as json_fp:
                task = Task.objects.get_or_create_json(json.load(json_fp), task_name)
            with open(join(task_dir, TASK_FILE)) as markdown_fp:
                task.description = markdown_fp.read()
            task.save()
        logger.info("Successfully imported %s", task_name)
    except Exception as e:
        logger.error("Importing task %s FAILED, exception follows.", task_name)
        logger.exception(e)
