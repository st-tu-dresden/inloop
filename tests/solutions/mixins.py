"""
Mixins for setting up test solutions data.

By convention, every password is set to "secret".
"""
from inloop.solutions.models import Solution
from inloop.tasks.models import Task

from tests.accounts.mixins import SimpleAccountsData


class SimpleTaskData:
    """
    Set up a simple task.
    """
    @classmethod
    def setUpTestData(cls):
        cls.task_fibonacci = Task.objects.create(
            pubdate="2000-01-01 00:00Z",
            system_name="task_fibonacci",
            slug="https://example.com/fibonacci/",
            category_id=1337,
            title="Fibonacci"
        )
        cls.task_leetspeak = Task.objects.create(
            pubdate="1970-01-01 00:00Z",
            system_name="task_leetspeak",
            slug="https://example.com/leetspeak/",
            category_id=1337,
            title="Leetspeak"
        )


class SolutionsData(SimpleAccountsData, SimpleTaskData):
    """
    Set up simple solutions.
    """
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.failed_solution = Solution.objects.create(
            author=cls.bob,
            task=cls.task_fibonacci,
            passed=False,
        )
        cls.passed_solution = Solution.objects.create(
            author=cls.alice,
            task=cls.task_fibonacci,
            passed=True,
        )
