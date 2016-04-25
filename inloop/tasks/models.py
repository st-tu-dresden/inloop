import re
from os.path import dirname, join

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.transaction import atomic
from django.utils import timezone
from django.utils.text import slugify
from huey.contrib.djhuey import db_task

from inloop.accounts.models import UserProfile
from inloop.gh_import.utils import parse_date
from inloop.tasks.checker import DockerSubProcessChecker


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
        instance.solution.task.slug,
        # FIXME: race condition at minute boundary causes files to be saved in different dirs
        # FIXME: don't use timezone.now(), use submission_date instead
        timezone.now().strftime('%Y/%m/%d/%H_%M_') + str(instance.solution.id),
        filename
    )
    return path


@db_task()
def check_solution(solution_id):
    """
    Huey job which calls TaskSolution.do_check() for the TaskSolution specified
    by solution_id.

    This function will not block, instead it submits the job to the queue
    and returns an AsyncData object immediately.

    Blocking behavior can be achieved by calling check_solution.call_local(),
    which circumvents the huey queue.

    The job's return value will be the id of the created CheckerResult.
    """
    #
    # model ids are used here since parameters and return values of huey
    # jobs have to be simple types (e.g., int)
    #
    solution = TaskSolution.objects.get(pk=solution_id)
    checker = DockerSubProcessChecker(settings.CHECKER, settings.DOCKER_IMAGE)
    result = solution.do_check(checker)
    return result.id


class TaskCategoryManager(models.Manager):
    def get_or_create(self, name):
        """Retrieve TaskCategory if it exists, create it otherwise."""
        try:
            return self.get(name=name)
        except ObjectDoesNotExist:
            return self.create(name=name, short_id=slugify(name))


# FIXME: __repr__ vs __str__
class TaskCategory(models.Model):
    # FIXME: that's a slug
    short_id = models.CharField(
        unique=True,
        max_length=50,
        help_text='Short ID for URLs'
    )
    name = models.CharField(
        unique=True,
        max_length=50,
        help_text='Category Name'
    )
    image = models.ImageField(null=True, upload_to='images/category_thumbs/')
    objects = TaskCategoryManager()

    def save(self, *args, **kwargs):
        self.short_id = slugify(self.name)
        super(TaskCategory, self).save(*args, **kwargs)

    def completed_tasks_for_user(self, user):
        """Return tasks of this category a user has already solved."""
        return self.task_set.filter(
            tasksolution__author=user,
            tasksolution__passed=True
        ).distinct()

    def published_tasks(self):
        """Return tasks of this category that have already been published."""
        return self.task_set.filter(publication_date__lt=timezone.now())

    def __str__(self):
        return self.name


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


# FIXME: add creation/update timestamp
# FIXME: auto slugify
# FIXME: __repr__ vs __str__
# FIXME: some fields should be blankable
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

    def is_published(self):
        """Returns True if the task is already visible to the users."""
        return timezone.now() > self.publication_date

    def task_location(self):
        return join(settings.MEDIA_ROOT, 'exercises', self.slug)

    def __str__(self):
        return self.name


# FIXME: default values
# FIXME: __repr__ vs __str__
class TaskSolution(models.Model):
    """
    Represents the user uploaded files.

    After a solution has been checked, a CheckerResult will be created for it. In
    other words, a TaskSolution without a CheckerResult has a pending asynchronous
    checker job.
    """

    submission_date = models.DateTimeField(help_text='When was the solution submitted?')
    author = models.ForeignKey(UserProfile)
    task = models.ForeignKey(Task)
    passed = models.BooleanField(default=False)

    def solution_path(self):
        if self.tasksolutionfile_set.count() < 1:
            raise ValueError("No files associated to TaskSolution(id=%d)" % self.id)

        # derive the directory from the first associated TaskSolutionFile
        solution_file = self.tasksolutionfile_set.first()
        return join(dirname(solution_file.file_path()))

    def do_check(self, checker):
        """
        Check this solution using the specified checker.

        If the checker returns normally, a CheckerResult (possibly containing one or
        more CheckerOutputs) will be saved to the database and returned.

        This method will block until the checker is finished. For this reason, views
        should call it through the asynchronous check_solution() wrapper, otherwise
        the whole request will get stuck.
        """
        result_tuple = checker.check_task(self.task.name, self.solution_path())

        with atomic():
            result = CheckerResult.objects.create(
                solution=self,
                stdout=result_tuple.stdout,
                stderr=result_tuple.stderr,
                return_code=result_tuple.rc,
                time_taken=result_tuple.duration
            )
            result.checkeroutput_set = [
                CheckerOutput(name=k, output=v) for k, v in result_tuple.file_dict.items()
            ]
            self.passed = result.is_success()
            self.save()

        return result

    def __str__(self):
        return "TaskSolution(author='{}', task='{}')".format(
            self.author.username,
            self.task
        )


class TaskSolutionFile(models.Model):
    '''Represents a single file as part of a solution'''

    solution = models.ForeignKey(TaskSolution)
    filename = models.CharField(max_length=50)
    file = models.FileField(upload_to=get_upload_path)

    def file_path(self):
        return self.file.path

    def __str__(self):
        return "TaskSolutionFile('%s')" % self.file


class CheckerResult(models.Model):
    """
    Saves low-level information about the checker execution.

    This currently includes the process' stdout, stderr, return code and wall time.
    """
    solution = models.ForeignKey(TaskSolution)
    created_at = models.DateTimeField(auto_now_add=True)
    stdout = models.TextField(default="")
    stderr = models.TextField(default="")
    return_code = models.SmallIntegerField(default=-1)
    time_taken = models.FloatField(default=0.0)

    # to be removed:
    passed = models.BooleanField(default=False)

    def user(self):
        return self.solution.author

    def task(self):
        return self.solution.task

    def is_success(self):
        return self.return_code == 0

    def __str__(self):
        return "CheckerResult(solution_id=%d, passed=%s)" % (self.solution.id, self.passed)


class CheckerOutput(models.Model):
    """
    Represents output of a checker execution step.

    A CheckerResult has multiple CheckerOutputs, for each step of a checker
    execution (for instance: compiler output, JUnit logs). This output is
    intended to be interpreted later by parsers/pretty printers/etc.
    """
    result = models.ForeignKey(CheckerResult)
    name = models.CharField(max_length=30)
    output = models.TextField()
