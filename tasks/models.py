from django.db import models
from django.utils import timezone
from accounts.models import UserProfile


class TaskCategory(models.Model):
    def save(self, *args, **kwargs):
        sid = getattr(self, 'short_id', False)
        setattr(self, 'short_id', sid.upper())
        super(TaskCategory, self).save(*args, **kwargs)

    short_id = models.CharField(
        unique=True,
        max_length=2,
        help_text='Short ID for the database')
    name = models.CharField(
        unique=True,
        max_length=50,
        help_text='Category Name')

    def get_tuple(self):
        return (self.short_id, self.name)

    def __str__(self):
        return self.short_id


class Task(models.Model):
    '''
    Represents the tasks that are presented to the user to solve.
    '''

    title = models.CharField(
        max_length=100,
        help_text='Task name')
    author = models.ForeignKey(
        UserProfile)
    description = models.TextField(
        help_text='Task description')
    publication_date = models.DateTimeField(
        help_text='When should the task be published?')
    deadline_date = models.DateTimeField(
        help_text='Date the task is due to')
    category = models.ForeignKey(TaskCategory)
    slug = models.SlugField(
        max_length=50,
        unique=True,
        help_text='URL name')

    def is_active(self):
        '''
        Returns True if the task is already visible to the users.
        '''

        return timezone.now() > self.publication_date
