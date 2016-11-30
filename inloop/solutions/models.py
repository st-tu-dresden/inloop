from os.path import dirname, join

from django.db import models
from django.db.transaction import atomic
from django.urls import reverse
from django.utils import timezone

from inloop.accounts.models import UserProfile
from inloop.tasks.models import Task


def get_upload_path(obj, filename):
    solution = obj.solution
    return join(
        'solutions',
        solution.author.username,
        solution.task.slug,
        "%s_%s" % (solution.submission_date.strftime("%Y/%m/%d/%H_%M"), solution.id),
        filename
    )


class Solution(models.Model):
    """
    Represents the user uploaded files.

    After a solution has been checked, a CheckerResult will be created for it. In
    other words, a Solution without a CheckerResult has a pending asynchronous
    checker job.
    """

    submission_date = models.DateTimeField(
        help_text="When was the solution submitted?",
        auto_now_add=True
    )
    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    passed = models.BooleanField(default=False)

    # time after a solution without a CheckerResult is regarded as lost
    TIMEOUT = timezone.timedelta(minutes=5)

    def solution_path(self):
        if self.solutionfile_set.count() < 1:
            raise AssertionError("No files associated to Solution(id=%d)" % self.id)

        # derive the directory from the first associated SolutionFile
        solution_file = self.solutionfile_set.first()
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
        # XXX: have circular imports -> needs decoupling
        from inloop.testrunner.models import TestOutput, TestResult

        result_tuple = checker.check_task(self.task.name, self.solution_path())

        with atomic():
            result = TestResult.objects.create(
                solution=self,
                stdout=result_tuple.stdout,
                stderr=result_tuple.stderr,
                return_code=result_tuple.rc,
                time_taken=result_tuple.duration
            )
            result.testoutput_set.set([
                TestOutput(name=name, output=output)
                for name, output
                in result_tuple.file_dict.items()
            ], bulk=False, clear=True)
            self.passed = result.is_success()
            self.save()

        return result

    def get_absolute_url(self):
        return reverse("solutions:detail", kwargs={'solution_id': self.id})

    def __repr__(self):
        return "<%s: id=%r author=%r task=%r>" % \
            (self.__class__.__name__, self.id, str(self.author), str(self.task))

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

    def __str__(self):
        return "Solution #%d" % self.id


class SolutionFile(models.Model):
    '''Represents a single file as part of a solution'''

    solution = models.ForeignKey(Solution, on_delete=models.CASCADE)
    filename = models.CharField(max_length=50)
    file = models.FileField(upload_to=get_upload_path)

    def file_path(self):
        return self.file.path

    def __str__(self):
        return str(self.file)
