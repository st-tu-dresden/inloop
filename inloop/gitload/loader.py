import json
import logging

from inloop.gitload.signals import repository_loaded
from inloop.tasks.models import Category, Task

try:
    from json import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

logger = logging.getLogger(__name__)


class InvalidTask(Exception):
    pass


def load_tasks(repository):
    repository.synchronize()
    repository.call_make()
    for task_file in repository.find_files("*/task.md"):
        try:
            load_task(task_file)
        except InvalidTask as e:
            logger.error("%s", e)
    repository_loaded.send(__name__, repository=repository)


def load_task(task_file):
    task_dir = task_file.parent
    meta = parse_metafile(task_dir)
    if meta.get("disabled"):
        return
    try:
        with task_file.open() as fp:
            update_or_create(task_dir, meta, fp.read())
    except KeyError as e:
        raise InvalidTask("%s: missing required field %s" % (task_dir.name, e))


def update_or_create(task_dir, meta, task_text):
    category, _ = Category.objects.get_or_create(name=meta["category"])
    Task.objects.update_or_create(system_name=task_dir.name, defaults={
        "category": category,
        "title": meta["title"],
        "pubdate": meta["pubdate"],
        "deadline": meta.get("deadline"),
        "description": task_text,
    })


def parse_metafile(task_dir):
    try:
        with task_dir.joinpath("meta.json").open() as fp:
            return json.load(fp)
    except JSONDecodeError as e:
        raise InvalidTask("%s: malformed meta.json (%s)" % (task_dir.name, e))
    except FileNotFoundError:
        raise InvalidTask("%s: missing meta.json" % task_dir.name)
