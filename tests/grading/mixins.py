"""
Mixins for setting up test plagiarism test data.
"""

from inloop.grading.models import DetectedPlagiarism, PlagiarismTest
from inloop.solutions.models import Solution

from tests.accounts.mixins import SimpleAccountsData
from tests.solutions.mixins import SimpleTaskData


class PlagiatedSolutionsData(SimpleAccountsData, SimpleTaskData):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.failed_solution_alice = Solution.objects.create(
            author=cls.alice,
            task=cls.task,
            passed=False,
        )
        cls.failed_solution_bob = Solution.objects.create(
            author=cls.bob,
            task=cls.task,
            passed=False,
        )
        cls.passed_solution_alice = Solution.objects.create(
            author=cls.alice,
            task=cls.task,
            passed=True,
        )
        cls.passed_solution_bob = Solution.objects.create(
            author=cls.bob,
            task=cls.task,
            passed=True,
        )


class PlagiarismTestData(PlagiatedSolutionsData):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.plagiarism_test = PlagiarismTest.objects.create()


class DetectedPlagiarismData(PlagiarismTestData):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.detected_plagiarism_alice = DetectedPlagiarism.objects.create(
            test=cls.plagiarism_test,
            solution=cls.passed_solution_alice,
        )
        cls.detected_plagiarism_bob = DetectedPlagiarism.objects.create(
            test=cls.plagiarism_test,
            solution=cls.passed_solution_bob,
        )
