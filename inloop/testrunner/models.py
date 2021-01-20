from __future__ import annotations

import signal

from django.conf import settings
from django.db import models
from django.db.transaction import atomic

from huey.contrib.djhuey import db_task

from inloop.solutions.models import Solution
from inloop.testrunner.runner import DockerTestRunner


@db_task()
def check_solution_async(solution_id: int) -> int:
    """
    Submit a job to check the solution specified by the given solution id.

    This function will not block, instead it returns an AsyncData object
    immediately. Blocking behavior can be achieved by calling
    `check_solution()`, which circumvents the huey queue.

    The job's return value will be the id of the created TestResult.
    """
    return check_solution(Solution.objects.get(pk=solution_id)).id


def check_solution(solution: Solution) -> TestResult:
    """
    Check the given solution with the test runner and return a TestResult.

    This function will block until the test runner has finished.
    """
    runner = DockerTestRunner(settings.TESTRUNNER_OPTIONS)
    test_output = runner.check_task(solution.task.system_name, str(solution.path))
    with atomic():
        test_result = TestResult.objects.create(
            solution=solution,
            stdout=test_output.stdout,
            stderr=test_output.stderr,
            return_code=test_output.rc,
            time_taken=test_output.duration,
        )
        TestOutput.objects.bulk_create(
            [
                TestOutput(result=test_result, name=name, output=content)
                for name, content in test_output.files.items()
            ]
        )
        solution.passed = test_result.is_success()
        solution.save()
    return test_result


class TestResult(models.Model):
    """
    Saves low-level information about test execution.

    This currently includes the process' stdout, stderr, return code and wall time.
    """

    solution = models.ForeignKey(Solution, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    stdout = models.TextField(default="")
    stderr = models.TextField(default="")
    return_code = models.SmallIntegerField(default=-1)
    time_taken = models.FloatField(default=0.0)

    def is_success(self) -> bool:
        return self.return_code == 0

    is_success.boolean = True
    is_success.short_description = "Successful"

    def status(self) -> str:
        if self.return_code == 0:
            return "success"
        if self.return_code == signal.SIGKILL:
            return "killed"
        if self.return_code in (125, 126, 127):
            return "error"
        return "failure"

    def __repr__(self) -> str:
        return f"<{type(self).__name__}: solution={self.solution_id} rc={self.return_code}>"

    def __str__(self) -> str:
        return f"Result #{self.id}"


class TestOutput(models.Model):
    """
    Represents output of a test execution step.

    A CheckerResult has multiple CheckerOutputs, for each step of a checker
    execution (for instance: compiler output, JUnit logs). This output is
    intended to be interpreted later by parsers/pretty printers/etc.
    """

    result = models.ForeignKey(TestResult, on_delete=models.CASCADE)
    name = models.CharField(max_length=60)
    output = models.TextField()

    def __str__(self) -> str:
        return self.name
