import signal

from django.db import models

from inloop.solutions.models import Solution


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

    def status(self):
        if self.return_code == 0:
            return "success"
        if self.return_code == signal.SIGKILL:
            return "killed"
        if self.return_code in (125, 126, 127):
            return "error"
        return "failure"

    def __repr__(self):
        return "<%s: solution_id=%r return_code=%r>" % \
            (self.__class__.__name__, self.solution_id, self.return_code)

    def __str__(self):
        return "Result #%s" % self.id


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

    def __str__(self):
        return self.name
