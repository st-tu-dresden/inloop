from __future__ import annotations

import os
from shutil import make_archive
from typing import Any, Set, Type

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from django.db.models.query import QuerySet
from django.db.models.signals import post_delete
from django.dispatch import receiver

from inloop.solutions.models import Solution


def zipfile_upload_path(test: PlagiarismTest, filename: str) -> str:
    """Return upload file paths for the PlagiarismTest.zip_file field."""
    timestamp = test.created_at.strftime("%Y%m%d-%H%M")
    return f"plagiarism_tests/jplag-results-{timestamp}.zip"


class PlagiarismTest(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    command = models.TextField(default="", help_text="Command that was used to perform the test")
    zip_file = models.FileField(upload_to=zipfile_upload_path, null=True)

    def __str__(self) -> str:
        return f"Plagiarism test #{self.id}"

    @property
    def all_detected_plagiarisms(self) -> QuerySet:
        """Get all detected plagiarisms for this test."""
        return self.detectedplagiarism_set.filter(veto=False)


@receiver(post_delete, sender=PlagiarismTest, dispatch_uid="delete_plagiarism_file")
def auto_delete_file_on_delete(
    sender: Type[PlagiarismTest], instance: PlagiarismTest, **kwargs: Any
) -> None:
    """
    Removes the zip file when its corresponding PlagiarismTest object is deleted.
    """
    if instance.zip_file and os.path.isfile(instance.zip_file.path):
        os.remove(instance.zip_file.path)


class DetectedPlagiarism(models.Model):
    test = models.ForeignKey(
        PlagiarismTest,
        on_delete=models.CASCADE,
        help_text="The test during which this plagiarism was detected",
    )
    solution = models.ForeignKey(
        Solution, on_delete=models.CASCADE, help_text="The solution that was found to be a rip-off"
    )
    veto = models.BooleanField(default=False, help_text="Cancel this detection")

    def __str__(self) -> str:
        return f"solution #{self.solution_id:d}"


def get_ripoff_tasks_for_user(user: User) -> QuerySet:
    """Return tasks for which rip-offs were detected for this user."""
    return (
        DetectedPlagiarism.objects.filter(solution__author=user, veto=False)
        .values_list("solution__task", flat=True)
        .distinct()
    )


def save_plagiarism_set(plagiarism_set: Set[Solution], result_dir: str) -> None:
    """Save the detected plagiarisms and zip file to the database."""
    path_to_zip = make_archive(result_dir, "zip", result_dir)
    with open(path_to_zip, mode="rb") as stream:
        zip_file = SimpleUploadedFile("jplag_test.zip", stream.read())
    test = PlagiarismTest.objects.create(zip_file=zip_file)
    DetectedPlagiarism.objects.bulk_create(
        [DetectedPlagiarism(test=test, solution=solution) for solution in plagiarism_set]
    )
