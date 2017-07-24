from django.db import models

from inloop.solutions.models import Solution


class PlagiarismTest(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    command = models.TextField(default="", help_text="Command that was used to perform the test")

    def __str__(self):
        return self.command


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


def ripoff_tasks_for_user(user):
    """Return tasks for which rip-offs were detected for this user."""
    return DetectedPlagiarism.objects.filter(
        solution__author=user, veto=False
    ).values_list("solution__task", flat=True).distinct()


def save_plagiarism_set(plagiarism_set):
    test = PlagiarismTest.objects.create()
    DetectedPlagiarism.objects.bulk_create([
        DetectedPlagiarism(test=test, solution=solution) for solution in plagiarism_set
    ])
