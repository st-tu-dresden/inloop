import re
import signal
from os.path import dirname, join

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import models
from django.db.transaction import atomic
from django.utils import timezone
from django.utils.text import slugify

from huey.contrib.djhuey import db_task

from inloop.accounts.models import UserProfile, get_system_user
from inloop.gh_import.utils import parse_date
from inloop.tasks.checker import DockerSubProcessChecker


def make_slug(value):
    """Extended slugify() that also removes '(...)' from strings.

    Example:
    >>> make_slug("Some Task III (winter term 2010/2011)")
    'some-task-iii'
    """
    return slugify(re.sub(r'\(.*?\)', '', value))


def get_upload_path(obj, filename):
    solution = obj.solution
    return join(
        'solutions',
        solution.author.username,
        solution.task.slug,
        "%s_%s" % (solution.submission_date.strftime("%Y/%m/%d/%H_%M"), solution.id),
        filename
    )


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
            return self.create(name=name, slug=slugify(name))


class TaskCategory(models.Model):
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
    objects = TaskCategoryManager()

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
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
        task.category = TaskCategory.objects.get_or_create(json['category'])
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
    author = models.ForeignKey(UserProfile)
    category = models.ForeignKey(TaskCategory)

    objects = TaskManager()

    def is_published(self):
        """Return True if the task is already visible to the users."""
        return timezone.now() > self.publication_date

    def is_expired(self):
        """Return True if the task has passed its optional deadline."""
        return self.deadline_date and timezone.now() > self.deadline_date

    def __str__(self):
        return self.name


class TaskSolution(models.Model):
    """
    Represents the user uploaded files.

    After a solution has been checked, a CheckerResult will be created for it. In
    other words, a TaskSolution without a CheckerResult has a pending asynchronous
    checker job.
    """

    submission_date = models.DateTimeField(
        help_text="When was the solution submitted?",
        auto_now_add=True
    )
    author = models.ForeignKey(UserProfile)
    task = models.ForeignKey(Task)
    passed = models.BooleanField(default=False)

    # time after a solution without a CheckerResult is regarded as lost
    TIMEOUT = timezone.timedelta(minutes=5)

    def solution_path(self):
        if self.tasksolutionfile_set.count() < 1:
            raise AssertionError("No files associated to TaskSolution(id=%d)" % self.id)

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
            result.checkeroutput_set.set([
                CheckerOutput(name=name, output=output)
                for name, output
                in result_tuple.file_dict.items()
            ], bulk=False, clear=True)
            self.passed = result.is_success()
            self.save()

        return result

    def get_absolute_url(self):
        return reverse("tasks:solutiondetail", kwargs={'solution_id': self.id})

    def __repr__(self):
        return "<%s: id=%r author=%r task=%r>" % \
            (self.__class__.__name__, self.id, str(self.author), str(self.task))

    def status(self):
        """
        Query the status of this TaskSolution.

        Possible states are: success, failure, error, lost, killed, pending. State
        `failure` means that a solution did not pass a test. In contrast to a
        `failure`, an `error` signals an internal, server-side bug or
        misconfiguration encountered during test execution.

        State `lost` means there was no response from the background queue
        after a reasonable amount of time.
        """
        result = self.checkerresult_set.last()
        if result:
            return result.status()
        if self.submission_date + self.TIMEOUT < timezone.now():
            return "lost"
        return "pending"

    def __str__(self):
        return "Solution #%d" % self.id


class TaskSolutionFile(models.Model):
    '''Represents a single file as part of a solution'''

    solution = models.ForeignKey(TaskSolution)
    filename = models.CharField(max_length=50)
    file = models.FileField(upload_to=get_upload_path)

    def file_path(self):
        return self.file.path

    def __str__(self):
        return str(self.file)


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

    def is_success(self):
        return self.return_code == 0

    is_success.boolean = True
    is_success.short_description = "Successful"

    def runtime(self):
        return "%.2f" % self.time_taken

    runtime.admin_order_field = "time_taken"
    runtime.short_description = "Runtime (seconds)"

    def __repr__(self):
        return "<%s: solution_id=%r return_code=%r>" % \
            (self.__class__.__name__, self.solution_id, self.return_code)

    def status(self):
        if self.return_code == 0:
            return "success"
        if self.return_code == signal.SIGKILL:
            return "killed"
        if self.return_code in (125, 126, 127):
            return "error"
        return "failure"

    def __str__(self):
        return "Result #%s" % self.id


class CheckerOutput(models.Model):
    """
    Represents output of a checker execution step.

    A CheckerResult has multiple CheckerOutputs, for each step of a checker
    execution (for instance: compiler output, JUnit logs). This output is
    intended to be interpreted later by parsers/pretty printers/etc.
    """
    result = models.ForeignKey(CheckerResult)
    name = models.CharField(max_length=60)
    output = models.TextField()

    def __str__(self):
        return self.name
