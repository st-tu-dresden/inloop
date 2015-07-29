from os.path import join

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from inloop.accounts.models import UserProfile
from inloop.gh_import.utils import parse_date


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
        try:
            task = self.get(name=name)
        except ObjectDoesNotExist:
            task = Task(name=name)
        return self._update_task(task, json)

    def _update_task(self, task, json):
        self._validate(json)
        task.title = json['title']
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
    '''Represents the tasks that are presented to the user to solve.'''

    title = models.CharField(max_length=100, help_text='Task title')
    name = models.CharField(max_length=100, help_text='Internal task name')
    author = models.ForeignKey(UserProfile)
    description = models.TextField(help_text='Task description')
    publication_date = models.DateTimeField(
        help_text='When should the task be published?')
    deadline_date = models.DateTimeField(help_text='Date the task is due to')
    category = models.ForeignKey(TaskCategory)
    slug = models.SlugField(
        max_length=50,
        unique=True,
        help_text='URL name')
    objects = TaskManager()

    def is_active(self):
        '''Returns True if the task is already visible to the users.'''

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
