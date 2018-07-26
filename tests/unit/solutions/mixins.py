"""
Mixins for setting up test solutions data.

By convention, every password is set to "secret".
"""
from inloop.solutions.models import Solution
from inloop.tasks.models import Task

from tests.unit.accounts.mixins import SimpleAccountsData


class SimpleTaskData:
    """
    Set up a simple task.
    """
    @classmethod
    def setUpTestData(cls):
        cls.task = Task.objects.create(
            pubdate="2000-01-01 00:00Z",
            category_id=1337,
            title="Fibonacci"
        )


class SolutionsData(SimpleAccountsData, SimpleTaskData):
    """
    Set up two solutions, one of which failed
    and the other one succeeded.
    """
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.failed_solution = Solution.objects.create(
            author=cls.bob,
            task=cls.task,
            passed=False,
        )
        cls.passed_solution = Solution.objects.create(
            author=cls.alice,
            task=cls.task,
            passed=True,
        )
