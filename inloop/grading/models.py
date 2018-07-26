import os
from shutil import make_archive

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver

from inloop.solutions.models import Solution


def get_upload_path(obj, filename):
    """
    Return an upload file path.

    All Plagiarism Test zip files will be stored in a shared directory.
    """
    return "plagiarism_tests/{created_at}/{filename}".format_map({
        "created_at": obj.created_at,
        "filename": filename,
    })


class PlagiarismTest(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    command = models.TextField(default="", help_text="Command that was used to perform the test")
    zip_file = models.FileField(upload_to=get_upload_path, null=True)

    def __str__(self):
        return "Plagiarism test #{}".format(self.id)

    @property
    def all_detected_plagiarisms(self):
        """
        Get all detected plagiarisms to this Test.
        """
        return DetectedPlagiarism.objects.filter(test=self, veto=False)


@receiver(post_delete, sender=PlagiarismTest, dispatch_uid="delete_plagiarism_file")
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes the zip file
    when its corresponding PlagiarismTest object is deleted.
    """
    if instance.zip_file:
        if os.path.isfile(instance.zip_file.path):
            os.remove(instance.zip_file.path)


class DetectedPlagiarism(models.Model):
    test = models.ForeignKey(
        PlagiarismTest, on_delete=models.CASCADE,
        help_text="The test during which this plagiarism was detected"
    )
    solution = models.ForeignKey(
        Solution, on_delete=models.CASCADE,
        help_text="The solution that was found to be a rip-off"
    )
    veto = models.BooleanField(default=False, help_text="Cancel this detection")

    def __str__(self):
        return "solution #%d" % self.solution_id


def get_ripoff_tasks_for_user(user):
    """Return tasks for which rip-offs were detected for this user."""
    return DetectedPlagiarism.objects.filter(
        solution__author=user, veto=False
    ).values_list("solution__task", flat=True).distinct()


def save_plagiarism_set(plagiarism_set, result_dir):
    """Save the detected plagiarisms to the database and assign the zipped output"""
    path_to_zip = make_archive(result_dir, "zip", result_dir)
    with open(path_to_zip, 'rb') as zip_data:
        zip_file = SimpleUploadedFile("jplag_test.zip", zip_data.read())
    test = PlagiarismTest.objects.create(
        zip_file=zip_file
    )
    DetectedPlagiarism.objects.bulk_create([
        DetectedPlagiarism(test=test, solution=solution) for solution in plagiarism_set
    ])
