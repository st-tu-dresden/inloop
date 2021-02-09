from __future__ import annotations

import logging
import os
import string
from contextlib import suppress
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Type, Union
from zipfile import ZIP_DEFLATED, ZipFile

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile, UploadedFile
from django.db import IntegrityError, models
from django.db.models import QuerySet
from django.db.models.aggregates import Max
from django.db.models.functions import Coalesce
from django.db.models.signals import post_delete
from django.db.transaction import atomic
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from constance import config
from huey.contrib.djhuey import db_task, lock_task

from inloop.solutions.signals import solution_submitted
from inloop.solutions.validators import validate_filenames
from inloop.tasks.models import Task

hash_chars = string.digits + string.ascii_lowercase[:22]

logger = logging.getLogger(__name__)


def hash32(obj: Union[str, User]) -> str:
    """Map the given object to one of 32 possible characters."""
    # take advantage of Python's string hashing
    return hash_chars[hash(str(obj)) % 32]


def get_upload_path(obj: SolutionFile, filename: str) -> str:
    """
    Return an upload file path.
    All files related to a specific solution will share a common base directory.
    """
    s = obj.solution
    return "solutions/{year}/{slug}/{hash}/{id}/{filename}".format_map(
        {
            "year": s.submission_date.year,
            "slug": s.task.slug,
            # another "random" level to avoid too many files per slug directory
            "hash": hash32(s.author),
            "id": s.id,
            "filename": filename,
        }
    )


def get_prunable_solutions(
    *, users: Iterable[User], tasks: Iterable[Task], max_keep: int
) -> Iterator[QuerySet]:
    """
    Yield querysets of solutions that can be deleted if only max_keep solutions
    should be retained per user and task of the given user and task querysets.

    `max_keep` should be chosen such that it is not smaller than the current
    highest submission limit for a task, because this breaks some assumptions
    made about counting the submissions.
    """
    for user in users:
        for task in tasks:
            solutions = Solution.objects.filter(task=task, author=user)
            solutions_to_keep = solutions.order_by("-id")[:max_keep]
            yield solutions.exclude(id__in=solutions_to_keep)


def get_archive_upload_path(solution: Solution, filename: str) -> str:
    """
    Return an upload file path of the archive
    generated from a given solution.
    """
    return f"archives/{solution.author}/{solution.id}/{filename}"


def create_archive(solution: Solution) -> None:
    """
    Create zip archive of all files associated with a solution.
    """
    if solution.archive:
        return
    stream = BytesIO()
    stream.name = f"Solution_{solution.scoped_id}_{solution.task.underscored_title}.zip"
    with ZipFile(stream, mode="w", compression=ZIP_DEFLATED) as zipfile:
        for solution_file in solution.solutionfile_set.all():
            zipfile.write(filename=solution_file.absolute_path, arcname=solution_file.name)
    solution.archive = SimpleUploadedFile(
        name=stream.name, content=stream.getvalue(), content_type="application/zip"
    )
    solution.save()


@db_task()
def create_archive_async(solution: Solution) -> None:
    """
    Create zip archive of all files associated with a solution asynchronously.
    """
    with lock_task(solution.id):
        create_archive(solution)


class SubmissionError(Exception):
    """
    Used by submit(…) to signal user error conditions that can occur during
    a submission, such as passed deadlines, missing files, and so on.
    """


def submit(files: Iterable[UploadedFile], author: User, task: Task) -> None:
    """
    Perform the core workflow of a solution submit: validate it, save it to
    the DB and propagate the event to other components (e.g., the testrunner).
    """
    if task.is_expired:
        raise SubmissionError("The deadline for this task has passed.")
    if not files:
        raise SubmissionError("You haven't uploaded any files.")
    _check_submission_limit(author, task)
    try:
        validate_filenames([file.name for file in files])
        solution = _atomic_submit(files, author, task)
        if config.IMMEDIATE_FEEDBACK:
            solution_submitted.send(sender=__name__, solution=solution)
    except IntegrityError:
        logger.exception("db constraint violation occurred")
        raise SubmissionError("Concurrent submission is not possible.")


def _check_submission_limit(author: User, task: Task) -> None:
    """
    Ensure that the author is within the submission limit for the task (if any).
    """
    if task.has_submission_limit:
        count = Solution.objects.filter(author=author, task=task).count()
        limit = task.submission_limit
        if count >= limit:
            suffix = "" if limit == 1 else "s"
            raise SubmissionError(f"You cannot submit more than {limit} solution{suffix}.")


@atomic
def _atomic_submit(files: Iterable[UploadedFile], author: User, task: Task) -> Solution:
    """Save all submission objects in a single database transaction."""
    solution = Solution.objects.create(author=author, task=task)
    SolutionFile.objects.bulk_create(
        [SolutionFile(solution=solution, file=file) for file in files]
    )
    return solution


class Solution(models.Model):
    """
    Represents the user uploaded files.

    After a solution has been checked, a CheckerResult will be created for it. In
    other words, a Solution without a CheckerResult has a pending asynchronous
    checker job.
    """

    scoped_id = models.PositiveIntegerField(
        help_text="Solution id unique for task and author", editable=False
    )
    submission_date = models.DateTimeField(
        help_text="When was the solution submitted?", auto_now_add=True
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    passed = models.BooleanField(default=False)

    archive = models.FileField(upload_to=get_archive_upload_path, blank=True, null=True)

    # time after a solution without a CheckerResult is regarded as lost
    TIMEOUT = timezone.timedelta(minutes=5)

    class Meta:
        unique_together = ("author", "scoped_id", "task")
        index_together = ["author", "scoped_id", "task"]

    @property
    def path(self) -> Path:
        # derive the directory from the first associated SolutionFile
        solution_file = self.solutionfile_set.first()
        if not solution_file:
            raise AssertionError(f"Empty solution: {self!r}")
        return solution_file.absolute_path.parent

    def get_absolute_url(self) -> str:
        return reverse("solutions:staffdetail", kwargs={"id": self.id})

    def status(self) -> str:
        """
        Query the status of this Solution.

        Possible states are: saved, success, failure, error, lost, killed, pending.
        State `failure` means that a solution did not pass a test. In contrast to a
        `failure`, an `error` signals an internal, server-side bug or
        misconfiguration encountered during test execution.

        State `lost` means there was no response from the background queue
        after a reasonable amount of time.
        """
        if not config.IMMEDIATE_FEEDBACK:
            return "saved"
        result = self.testresult_set.last()
        if result:
            return result.status()
        if self.submission_date + self.TIMEOUT < timezone.now():
            return "lost"
        return "pending"

    def get_next_scoped_id(self) -> int:
        """Compute the next scoped_id."""
        query = Solution.objects.filter(author=self.author, task=self.task).aggregate(
            next_scoped_id=(Coalesce(Max("scoped_id"), 0) + 1)
        )
        return query["next_scoped_id"]

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Save this solution and ensure a scoped_id is assigned.
        Calculation and storage of scoped_id is not atomic, callers
        should be prepared to handle the resulting IntegrityError
        when they use this method in a concurrent fashion (e.g., in
        web requests).
        """
        if not self.scoped_id:
            self.scoped_id = self.get_next_scoped_id()
        return super().save(*args, **kwargs)

    def __repr__(self) -> str:
        return "<%s: id=%r author=%r task=%r>" % (
            self.__class__.__name__,
            self.id,
            str(self.author),
            str(self.task),
        )

    def __str__(self) -> str:
        return f"Solution #{self.id:d}"


@receiver(post_delete, sender=Solution, dispatch_uid="delete_solutionfile")
def auto_delete_archive_on_delete(
    sender: Type[Solution], instance: Solution, **kwargs: Any
) -> None:
    """
    Removes archive from filesystem when corresponding Solution object is deleted.
    """
    if instance.archive and os.path.isfile(instance.archive.path):
        with suppress(PermissionError):
            os.remove(instance.archive.path)


class SolutionFile(models.Model):
    """Represents a single file as part of a solution."""

    solution = models.ForeignKey(Solution, on_delete=models.CASCADE)
    file = models.FileField(upload_to=get_upload_path)

    @property
    def name(self) -> str:
        """Return the basename of the file."""
        return self.relative_path.name

    @property
    def relative_path(self) -> Path:
        """Return the file path relative to settings.MEDIA_ROOT."""
        return Path(self.file.name)

    @property
    def absolute_path(self) -> Path:
        """Return the absolute file path as seen on the file system."""
        return Path(self.file.path)

    @property
    def size(self) -> int:
        """Return the size of the file in bytes."""
        return self.absolute_path.stat().st_size

    @property
    def contents(self) -> str:
        with open(self.absolute_path, errors="replace") as stream:
            return stream.read()

    def __str__(self) -> str:
        return self.name


@receiver(post_delete, sender=SolutionFile, dispatch_uid="delete_solutionfile")
def auto_delete_file_on_delete(
    sender: Type[SolutionFile], instance: SolutionFile, **kwargs: Any
) -> None:
    """
    Removes file from filesystem when corresponding Solution object is deleted.
    """
    if instance.file and os.path.isfile(instance.file.path):
        with suppress(PermissionError):
            os.remove(instance.file.path)


@atomic
def create_checkpoint(files: Iterable[Dict], task: Task, user: User) -> None:
    validate_filenames([file["name"] for file in files])
    Checkpoint.objects.filter(author=user, task=task).delete()
    checkpoint = Checkpoint.objects.create(author=user, task=task)
    CheckpointFile.objects.bulk_create(
        [
            CheckpointFile(checkpoint=checkpoint, name=file["name"], contents=file["contents"])
            for file in files
        ]
    )


class Checkpoint(models.Model):
    """
    Represents an editor checkpoint.

    After the user saves his solution in the online code editor,
    a checkpoint is created. This checkpoint can be used to restore
    the last workstate in the online code editor.
    """

    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"task_id={self.task_id}, author_id={self.author_id}"


class CheckpointFile(models.Model):
    """Represents a single file as part of a checkpoint."""

    checkpoint = models.ForeignKey(Checkpoint, on_delete=models.CASCADE)
    name = models.TextField()
    contents = models.TextField()

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
