from django.db import models
from django.utils import timezone
from accounts.models import UserProfile


TASK_CATEGORIES = (('B', 'Basic Exercise'),
                   ('A', 'Advanced Exercise'),
                   ('L', 'Lesson Exercise'),
                   ('E', 'Exam Exercise'))


def get_task_categories():
    # TODO: CHECK LOGIC
    res = ()
    for c in TaskCategory.objects.all():
        res += c.get_tuple()
    return res


class TaskCategory(models.Model):
    short_id = models.CharField(
        max_length=2,
        help_text='Short ID for the database')
    name = models.CharField(
        max_length=50,
        help_text='Category Name')

    def get_tuple(self):
        return (self.short_id, self.name)


class Task(models.Model):
    '''
    Represents the tasks that are presented to the user to solve.
    '''

    def __init__(self, *args, **kwargs):
        super(Task, self).__init__(*args, **kwargs)
        self.category = models.CharField(
            max_length=1,
            choices=get_task_categories,
            help_text='Task category')

    title = models.CharField(max_length=100, help_text='Task name')
    author = models.ForeignKey(UserProfile)
    description = models.TextField(help_text='Task description')
    publication_date = models.DateTimeField(
        help_text='When should the task be published?'
    )
    deadline_date = models.DateTimeField(help_text='Date the task is due to')
    # category = models.CharField(max_length=1,
    #                            choices=TASK_CATEGORIES,
    #                            help_text='Category of task')
    category = models.OneToOneField(TaskCategory)
    slug = models.SlugField(max_length=50, unique=True, help_text='URL name')

    def is_active(self):
        '''
        Returns True if the task is already visible to the users.
        '''

        return timezone.now() > self.publication_date


# class TaskSolutionFile(models.Model):
#     '''
#     Represents the files the user has to edit for each task. As each task
#     has a different amount of connected files, they were implemented using
#     a ForeignKey relationship.
#
#     Access all files connected to a task:
#     task = Task.objects.get(pk=1)
#     task.task_files.all()
#     '''
#     filename = models.CharField(
#         max_length=30, help_text='Name of the file including the ending'
#     )
#     unittest = models.BooleanField()
#     content = models.TextField()
#     task = models.ForeignKey(Task, related_name='task_files')
