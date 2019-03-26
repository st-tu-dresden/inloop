from unittest.mock import Mock

from django.test import TestCase
from django.utils import timezone

from inloop.solutions.models import Solution, get_upload_path

from tests.solutions.mixins import SolutionsData


class SolutionsModelTest(SolutionsData, TestCase):
    def test_precondition(self):
        """Verify there are no results before checking."""
        self.assertEqual(self.failed_solution_alice.testresult_set.count(), 0)
        self.assertFalse(self.failed_solution_alice.passed)

    def test_get_upload_path(self):
        """Test the upload path for solution files."""

        # Create a mock solution to check its
        # computed upload path
        mock = Mock()
        mock.solution.submission_date.year = "1970"
        mock.solution.task.slug = "here-be-dragons"
        mock.solution.author = "Mr. Mustermann"
        mock.solution.id = "123456"

        upload_path = get_upload_path(mock, "Fibonacci.java")
        self.assertTrue(upload_path.startswith("solutions"))
        self.assertTrue(upload_path.endswith("Fibonacci.java"))

        tokens = upload_path.split("/")
        for token in ["1970", "here-be-dragons", "123456"]:
            self.assertTrue(token in tokens)

    def test_solution_default_status(self):
        """Verify that the default status of a solution is pending."""

        # Both failed_solution and passed_solution were not checked yet
        # so their status should be pending
        self.assertEqual(self.failed_solution_alice.status(), "pending")
        self.assertEqual(self.passed_solution_alice.status(), "pending")

    def test_solution_lost_status(self):
        """
        Verify that a solution is lost when it was not processed
        in a reasonable amount of time.
        """
        delayed_solution = Solution.objects.create(
            author=self.bob,
            task=self.published_task1,
            passed=False,
        )
        # Simulate that the solution was submitted one hour ago.
        # The solution should therefore be marked as lost.
        mocked_time = timezone.now() - timezone.timedelta(hours=1)
        delayed_solution.submission_date = mocked_time
        self.assertEqual(delayed_solution.status(), "lost")
