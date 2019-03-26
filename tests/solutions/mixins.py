"""
Mixins for setting up test solutions data.

By convention, every password is set to "secret".
"""
from inloop.solutions.models import Solution

from tests.accounts.mixins import SimpleAccountsData
from tests.tasks.mixins import TaskData


class SolutionsData(SimpleAccountsData, TaskData):
    """
    Set up simple solutions.
    """
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
