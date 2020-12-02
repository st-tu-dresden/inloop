"""
Mixins for setting up test solutions data.

By convention, every password is set to "secret".
"""
from inloop.solutions.models import Solution
from inloop.tasks.models import Category, Task

from tests.accounts.mixins import SimpleAccountsData
from tests.tasks.mixins import TaskData


class SimpleTaskData:
    """
    Set up a simple task and assign a category.
    """

    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(id=1337, name="Test Category")
        cls.task = Task.objects.create(
            pubdate="2000-01-01 00:00Z", category_id=1337, title="Fibonacci", slug="task"
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
            task=cls.task,
            passed=False,
        )
        cls.passed_solution = Solution.objects.create(
            author=cls.alice,
            task=cls.task,
            passed=True,
        )


class PassedSolutionsData(SimpleAccountsData, TaskData):
    """Set up simple passed solutions."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.passed_solution_alice = Solution.objects.create(
            author=cls.alice,
            task=cls.published_task1,
            passed=True,
        )
        cls.passed_solution_bob = Solution.objects.create(
            author=cls.bob,
            task=cls.published_task1,
            passed=True,
        )


class FailedSolutionsData(SimpleAccountsData, TaskData):
    """Set up simple failed solutions."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.failed_solution_alice = Solution.objects.create(
            author=cls.alice,
            task=cls.published_task1,
            passed=False,
        )
        cls.failed_solution_bob = Solution.objects.create(
            author=cls.bob,
            task=cls.published_task1,
            passed=False,
        )
