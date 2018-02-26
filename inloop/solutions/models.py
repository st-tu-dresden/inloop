import string
from pathlib import Path

from django.conf import settings
from django.db import models
from django.db.models import Max
from django.db.transaction import atomic
from django.urls import reverse
from django.utils import timezone

from inloop.tasks.models import Task

hash_chars = string.digits + string.ascii_lowercase[:22]


def hash32(obj):
    """Map the given object to one of 32 possible characters."""
    # take advantage of Python's string hashing
    return hash_chars[hash(str(obj)) % 32]


def get_upload_path(obj, filename):
    """
    Return an upload file path.

    All files related to a specific solution will share a common base directory.
    """
    s = obj.solution
    return "solutions/{year}/{slug}/{hash}/{id}/{filename}".format_map({
        "year": s.submission_date.year,
        "slug": s.task.slug,
        # another "random" level to avoid too many files per slug directory
        "hash": hash32(s.author),
        "id": s.id,
        "filename": filename
    })


class Solution(models.Model):
    """
    Represents the user uploaded files.

    After a solution has been checked, a CheckerResult will be created for it. In
    other words, a Solution without a CheckerResult has a pending asynchronous
    checker job.
    """

    scoped_id = models.PositiveIntegerField(
        help_text="Solution id unique for task and author",
        editable=False
    )
    submission_date = models.DateTimeField(
        help_text="When was the solution submitted?",
        auto_now_add=True
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    passed = models.BooleanField(default=False)

    # time after a solution without a CheckerResult is regarded as lost
    TIMEOUT = timezone.timedelta(minutes=5)

    class Meta:
        unique_together = ("author", "scoped_id", "task")
        index_together = ["author", "scoped_id", "task"]

    @property
    def path(self):
        # derive the directory from the first associated SolutionFile
        solution_file = self.solutionfile_set.first()
        if not solution_file:
            raise AssertionError("Empty solution: %r" % self)
        return solution_file.absolute_path.parent

    def get_absolute_url(self):
        return reverse("solutions:staffdetail", kwargs={'id': self.id})

    def status(self):
        """
        Query the status of this Solution.

        Possible states are: success, failure, error, lost, killed, pending. State
        `failure` means that a solution did not pass a test. In contrast to a
        `failure`, an `error` signals an internal, server-side bug or
        misconfiguration encountered during test execution.

        State `lost` means there was no response from the background queue
        after a reasonable amount of time.
        """
        result = self.testresult_set.last()
        if result:
            return result.status()
        if self.submission_date + self.TIMEOUT < timezone.now():
            return "lost"
        return "pending"

    @atomic
    def save(self, *args, **kwargs):
        if not self.scoped_id:
            current_max = Solution.objects.filter(
                author=self.author, task=self.task
            ).aggregate(Max("scoped_id"))["scoped_id__max"]
            self.scoped_id = (current_max or 0) + 1
        return super().save(*args, **kwargs)

    def __repr__(self):
        return "<%s: id=%r author=%r task=%r>" % \
            (self.__class__.__name__, self.id, str(self.author), str(self.task))

    def __str__(self):
        return "Solution #%d" % self.id


class SolutionFile(models.Model):
    """Represents a single file as part of a solution."""

    solution = models.ForeignKey(Solution, on_delete=models.CASCADE)
    file = models.FileField(upload_to=get_upload_path)

    @property
    def name(self):
        """Return the basename of the file."""
        return self.relative_path.name

    @property
    def relative_path(self):
        """Return the file path relative to settings.MEDIA_ROOT."""
        return Path(self.file.name)

    @property
    def absolute_path(self):
        """Return the absolute file path as seen on the file system."""
        return Path(self.file.path)

    @property
    def size(self):
        """Return the size of the file in bytes."""
        return self.absolute_path.stat().st_size

    @property
    def contents(self):
        with self.absolute_path.open() as f:
            return f.read()

    def __str__(self):
        return self.name
