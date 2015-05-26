from os.path import join

from django.db import models
from django.utils import timezone

from accounts.models import UserProfile


def generate_short_id(s):
    s = ''.join(e for e in s if e.isalnum())
    return s.lower()


def get_upload_path(instance, filename):
    path = join(
        'solutions',
        instance.solution.author.username,
        instance.solution.task.title,
        timezone.now().strftime('%Y/%m/%d/%H:%M_') + str(instance.solution.id),
        filename)
    return path


class TaskCategory(models.Model):
    def save(self, *args, **kwargs):
        self.short_id = generate_short_id(self.name)
        super(TaskCategory, self).save(*args, **kwargs)

    short_id = models.CharField(
        unique=True,
        max_length=50,
        help_text='Short ID for URLs')
    name = models.CharField(
        unique=True,
        max_length=50,
        help_text='Category Name')
    image = models.ImageField(
        upload_to='images/category_thumbs/')

    def get_tuple(self):
        return (self.short_id, self.name)

    def completed_tasks_for_user(self, user):
        '''Returns the tasks a user has already solved.'''
        return [t for t in Task.objects.all() if t.solved_by(user)]

    def get_tasks(self):
        return Task.objects.filter(category=self)

    def __str__(self):
        return self.short_id


class Task(models.Model):
    '''Represents the tasks that are presented to the user to solve.'''

    title = models.CharField(
        max_length=100,
        help_text='Task name')
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

    def solved_by(self, user):
        queryset = TaskSolution.objects.filter(author=user, is_correct=True)
        return True if queryset else False

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
