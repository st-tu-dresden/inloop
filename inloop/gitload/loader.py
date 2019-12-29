import json
import logging
from json import JSONDecodeError

from inloop.gitload.signals import repository_loaded
from inloop.tasks.models import Category, Task

LOG = logging.getLogger(__name__)


class InvalidTask(Exception):
    pass


def load_tasks(repository):
    repository.synchronize()
    repository.call_make()
    for task_file in repository.find_files('*/task.md'):
        try:
            load_task(task_file)
        except InvalidTask as error:
            LOG.error('%s', error)
    repository_loaded.send(__name__, repository=repository)


def load_task(task_file):
    task_dir = task_file.parent
    meta = parse_metafile(task_dir)
    if meta.get('disabled'):
        return
    try:
        with open(task_file) as stream:
            update_or_create(task_dir, meta, stream.read())
    except KeyError as key:
        raise InvalidTask(f'{task_dir.name}: missing required field {key}')


def update_or_create(task_dir, meta, task_text):
    category, _ = Category.objects.get_or_create(name=meta['category'])
    Task.objects.update_or_create(system_name=task_dir.name, defaults={
        'category': category,
        'title': meta['title'],
        'pubdate': meta['pubdate'],
        'deadline': meta.get('deadline'),
        'description': task_text,
    })


def parse_metafile(task_dir):
    try:
        with open(task_dir / 'meta.json') as stream:
            return json.load(stream)
    except JSONDecodeError as error:
        raise InvalidTask(f'{task_dir.name}: malformed meta.json ({error})')
    except FileNotFoundError:
        raise InvalidTask(f'{task_dir.name}: missing meta.json')
