import itertools
import re

from django.db import models
from django.db.models.expressions import Value
from django.db.models.fields import BooleanField
from django.utils import timezone
from django.utils.text import slugify


class Category(models.Model):
    """Task categories may be used to arbitrarily group tasks."""

    class Meta:
        verbose_name_plural = 'Task categories'

    slug = models.SlugField(max_length=50, unique=True, help_text='URL name')
    name = models.CharField(unique=True, max_length=50, help_text='Category name')
    display_order = models.IntegerField(default=0, help_text='Display order (lower values first)')
    description = models.TextField(default='', help_text='Short category description')

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def completion_info(self, user):
        return self.task_set.completion_info(user)

    def __str__(self):
        return self.name


class TaskQuerySet(models.QuerySet):
    """Enhances QuerySet with convenience methods to get task completion status."""

    def unpublished(self):
        return self.filter(pubdate__gte=timezone.now())

    def published(self):
        return self.filter(pubdate__lt=timezone.now())

    def completed_by(self, user):
        return self.filter(solution__passed=True, solution__author=user).distinct()

    def not_completed_by(self, user):
        return self.exclude(id__in=self.completed_by(user).values('id'))

    def completed_by_values(self, user, sort_field):
        qs = self.order_by(sort_field)
        qs1 = qs.completed_by(user).annotate(completed=Value(True, BooleanField()))
        qs2 = qs.not_completed_by(user).annotate(completed=Value(False, BooleanField()))
        reverse = sort_field.startswith('-')
        sort_field = sort_field.lstrip('-')

        def keyfunc(task):
            return getattr(task, sort_field)

        return sorted(itertools.chain(qs1, qs2), key=keyfunc, reverse=reverse)

    def completion_info(self, user):
        qs = self.published()
        num_published = len(qs)
        if num_published > 0:
            num_completed = len(qs.completed_by(user))
            progress = round(num_completed / num_published * 100)
        else:
            num_completed = progress = 0
        return {
            'num_completed': num_completed,
            'num_published': num_published,
            'is_completed': num_completed == num_published,
            'progress': progress
        }


class Task(models.Model):
    """Represents the tasks that are presented to the user to solve."""

    class Meta:
        ordering = ['deadline', 'pubdate', 'title']

    # mandatory fields
    title = models.CharField(max_length=100, help_text='Task title')
    system_name = models.CharField(max_length=100, unique=True, help_text='Internally used name')
    slug = models.SlugField(max_length=50, unique=True, help_text='URL name')
    description = models.TextField(help_text='Task description')
    pubdate = models.DateTimeField(help_text='When should the task be published?')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    # autogenerated fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # optional fields
    deadline = models.DateTimeField(
        help_text='Optional date the task is due to',
        null=True,
        blank=True
    )

    objects = TaskQuerySet.as_manager()

    @property
    def is_published(self):
        """Return True if the task is already visible to the users."""
        return timezone.now() > self.pubdate

    @property
    def is_expired(self):
        """Return True if the task has passed its optional deadline."""
        return self.deadline and timezone.now() > self.deadline

    def is_completed_by(self, user):
        return self.id in Task.objects.completed_by(user).values_list('id', flat=True)

    @property
    def sluggable_title(self):
        """Return the title with anything between parentheses removed."""
        return re.sub(r'\(.*?\)', '', self.title)

    @property
    def underscored_title(self):
        """
        Return a sluggable title for this task
        with all whitespace replaced by underscores.
        """
        return self.sluggable_title.replace(' ', '_')

    def save(self, *args, **kwargs):
        self.slug = slugify(self.sluggable_title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
