import re

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from inloop.accounts.models import UserProfile, get_system_user
# XXX: dependency should be the other way around
from inloop.gh_import.utils import parse_date


def make_slug(value):
    """Extended slugify() that also removes '(...)' from strings.

    Example:
    >>> make_slug("Some Task III (winter term 2010/2011)")
    'some-task-iii'
    """
    return slugify(re.sub(r'\(.*?\)', '', value))


class CategoryManager(models.Manager):
    def get_or_create(self, name):
        """Retrieve Category if it exists, create it otherwise."""
        try:
            return self.get(name=name)
        except ObjectDoesNotExist:
            return self.create(name=name, slug=slugify(name))


class Category(models.Model):
    """Task categories may be used to arbitrarily group tasks."""

    class Meta:
        verbose_name_plural = "Task categories"

    slug = models.CharField(
        unique=True,
        max_length=50,
        help_text='Short ID for URLs'
    )
    name = models.CharField(
        unique=True,
        max_length=50,
        help_text='Category Name'
    )
    objects = CategoryManager()

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def completed_tasks_for_user(self, user):
        """Return tasks of this category a user has already solved."""
        return self.task_set.filter(
            solution__author=user,
            solution__passed=True
        ).distinct()

    def published_tasks(self):
        """Return tasks of this category that have already been published."""
        return self.task_set.filter(publication_date__lt=timezone.now())

    def __str__(self):
        return self.name


class TaskManager(models.Manager):
    meta_required = ['title', 'category', 'pubdate']

    def get_or_create_json(self, json, name):
        try:
            task = self.get(name=name)
        except ObjectDoesNotExist:
            task = Task(name=name, author=get_system_user())
        return self._update_task(task, json)

    def _update_task(self, task, json):
        self._validate(json)
        task.title = json['title']
        task.slug = make_slug(task.title)
        task.category = Category.objects.get_or_create(json['category'])
        task.publication_date = parse_date(json['pubdate'])
        try:
            task.deadline_date = parse_date(json['deadline'])
        except KeyError:
            task.deadline_date = None
        return task

    def _validate(self, json):
        missing = []
        for meta_key in self.meta_required:
            if meta_key not in json.keys():
                missing.append(meta_key)
        if missing:
            raise ValueError("Missing metadata keys: %s" % ", ".join(missing))


# FIXME: add creation/update timestamp
# FIXME: auto slugify
class Task(models.Model):
    """Represents the tasks that are presented to the user to solve."""

    # Mandatory fields:
    title = models.CharField(max_length=100, help_text='Task title')
    name = models.CharField(max_length=100, help_text='Internal task name')
    slug = models.SlugField(max_length=50, unique=True, help_text='URL name')
    description = models.TextField(help_text='Task description')
    publication_date = models.DateTimeField(help_text='When should the task be published?')

    # Optional fields:
    deadline_date = models.DateTimeField(
        help_text="Optional Date the task is due to",
        null=True,
        blank=True
    )

    # Foreign keys:
    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    objects = TaskManager()

    def is_published(self):
        """Return True if the task is already visible to the users."""
        return timezone.now() > self.publication_date

    def is_expired(self):
        """Return True if the task has passed its optional deadline."""
        return self.deadline_date and timezone.now() > self.deadline_date

    def __str__(self):
        return self.name
