"""
Mixins for setting up test plagiarism test data.
"""

from inloop.grading.models import DetectedPlagiarism, PlagiarismTest

from tests.solutions.mixins import SolutionsData


class PlagiarismTestData(SolutionsData):
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
