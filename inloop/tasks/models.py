import re
from os.path import join
from subprocess import Popen, PIPE
from shlex import split as shplit

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from inloop.accounts.models import UserProfile
from inloop.gh_import.utils import parse_date


def make_slug(value):
    """Extended slugify() that also removes '(...)' from strings.

    Example:
    >>> make_slug("Some Task III (winter term 2010/2011)")
    'some-task-iii'
    """
    return slugify(re.sub(r'\([^\)]+\)', '', value))


def get_upload_path(instance, filename):
    path = join(
        'solutions',
        instance.solution.author.username,
        instance.solution.task.title,
        timezone.now().strftime('%Y/%m/%d/%H:%M_') + str(instance.solution.id),
        filename)
    return path


class TaskCategoryManager(models.Manager):
    def get_or_create(self, name):
        """Retrieve TaskCategory if it exists, create it otherwise."""
        try:
            return self.get(name=name)
        except ObjectDoesNotExist:
            return self.create(name=name, short_id=slugify(name))


class TaskCategory(models.Model):
    short_id = models.CharField(
        unique=True,
        max_length=50,
        help_text='Short ID for URLs')
    name = models.CharField(
        unique=True,
        max_length=50,
        help_text='Category Name')
    image = models.ImageField(null=True, upload_to='images/category_thumbs/')
    objects = TaskCategoryManager()

    def save(self, *args, **kwargs):
        self.short_id = slugify(self.name)
        super(TaskCategory, self).save(*args, **kwargs)

    def get_tuple(self):
        return (self.short_id, self.name)

    def completed_tasks_for_user(self, user):
        '''Returns the tasks a user has already solved.'''
        return Task.objects.filter(tasksolution__author=user, tasksolution__is_correct=True)

    def get_tasks(self):
        '''Returns a queryset of this category's task that have already been
        published'''
        return Task.objects.filter(
            category=self,
            publication_date__lt=timezone.now())

    def __str__(self):
        return self.short_id


class MissingTaskMetadata(Exception):
    pass


class TaskManager(models.Manager):
    meta_required = ['title', 'category', 'pubdate']

    def get_or_create_json(self, json, name):
        author = UserProfile.get_system_user()
        try:
            task = self.get(name=name)
        except ObjectDoesNotExist:
            task = Task(name=name, author=author)
        return self._update_task(task, json)

    def _update_task(self, task, json):
        self._validate(json)
        task.title = json['title']
        task.slug = make_slug(task.title)
        task.category = TaskCategory.objects.get_or_create(json['category'])
        task.publication_date = parse_date(json['pubdate'])
        return task

    def _validate(self, json):
        missing = []
        for meta_key in self.meta_required:
            if meta_key not in json.keys():
                missing.append(meta_key)
        if missing:
            raise MissingTaskMetadata(missing)


class Task(models.Model):
    """Represents the tasks that are presented to the user to solve."""

    # Mandatory fields:
    title = models.CharField(max_length=100, help_text='Task title')
    name = models.CharField(max_length=100, help_text='Internal task name')
    slug = models.SlugField(max_length=50, unique=True, help_text='URL name')
    description = models.TextField(help_text='Task description')
    publication_date = models.DateTimeField(help_text='When should the task be published?')

    # Optional fields:
    deadline_date = models.DateTimeField(help_text='Date the task is due to', null=True)

    # Foreign keys:
    author = models.ForeignKey(UserProfile)
    category = models.ForeignKey(TaskCategory)

    objects = TaskManager()

    def is_active(self):
        """Returns True if the task is already visible to the users."""
        return timezone.now() > self.publication_date


class TaskSolution(models.Model):
    '''Represents the user uploaded files'''

    submission_date = models.DateTimeField(
        help_text='When was the solution submitted?')
    author = models.ForeignKey(UserProfile)
    task = models.ForeignKey(Task)
    is_correct = models.BooleanField(
        help_text='Did the checker accept the solution?',
        default=False)


class TaskSolutionFile(models.Model):
    '''Represents a single file as part of a solution'''

    solution = models.ForeignKey(TaskSolution)
    filename = models.CharField(max_length=50)
    file = models.FileField(upload_to=get_upload_path)


class Checker:
    def __init__(self, solution_path):
        self.test_cmd = "../gradlew -q -DsolutionPath={} test".format(solution_path)
        self.task_location = ''  # TODO: Get location of task (../gradlew call) from settings?

    def start(self):
        # TODO: Give container unique name during execution
        cmd = 'bash -c \"cd {} && {}'.format(self.task_location, self.test_cmd)
        self._container_build('docker-test').decode()
        result = self._container_execute(cmd=shplit(cmd), ctr_tag='docker-test', ctr_name='test')
        result = result.decode()
        self._parse_result(result)

    def _container_build(ctr_tag, path='.'):
        p = Popen(['timeout', '-s', 'SIGKILL', '30',
                   'docker', 'build', '-t', ctr_tag, '--rm=true', path],
                  stdout=PIPE)
        out = p.stdout.read()
        return out

    def _container_execute(self, cmd=[], ctr_tag, ctr_name, **mountpoints):
        # Add timeout to docker process
        popen_args = ['timeout', '-s', 'SIGKILL', '2']
        # Remove container after exit
        popen_args.extend(['docker', 'run', '--rm=true'])
        popen_args.extend(['--name', ctr_name])
        # Add mountpoints: {host: container} -> -v=host:container
        popen_args.extend(['-v={}:{}'.format(k, v) for k, v in mountpoints.items()])
        # Add the actual compilation and test command
        popen_args.extend(cmd)
        # Execute container
        p = Popen(popen_args, stdout=PIPE)
        out = p.stdout.read()

        if p.wait() == -9:  # Happens on timeout
            # We have to kill the container since it still runs
            # detached from Popen and we need to remove it after because
            # --rm is not working on killed containers
            self._kill_and_remove(ctr_name)

        return out

    def _kill_and_remove(ctr_name):
        for action in ('kill', 'rm'):
            p = Popen('docker %s %s' % (action, ctr_name), shell=True,
                      stdout=PIPE, stderr=PIPE)
            if p.wait() != 0:
                raise RuntimeError(p.stderr.read())

    def _parse_result(self):
        # create a CheckerResult
        pass
