from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import TestCase

from inloop.grading.management.commands import tud_export_bonuspoints_csv
from inloop.grading.management.commands.tud_export_bonuspoints_csv import filter_zeroes
from inloop.grading.models import DetectedPlagiarism, PlagiarismTest, get_ripoff_tasks_for_user
from inloop.grading.tud import calculate_grades, points_for_completed_tasks
from inloop.solutions.models import Solution

from tests.accounts.mixins import SimpleAccountsData
from tests.grading.mixins import DetectedPlagiarismData, PlagiarismTestData
from tests.solutions.mixins import PassedSolutionsData, SimpleTaskData, SolutionsData
from tests.tools import TemporaryMediaRootTestCase


def export_bonuspoints(category_name, date, zeroes=False):
    """Conveniently execute the bonus points export management command."""
    stdout = StringIO()
    with TemporaryDirectory() as path:
        output_path = Path(path).joinpath("output")
        args = [category_name, date.strftime("%Y-%m-%d"), output_path]
        call_command(
            tud_export_bonuspoints_csv.Command(), *args, stdout=stdout, zeroes=zeroes
        )

        with open(str(output_path), "r") as f:
            return stdout.getvalue(), f.readlines(), output_path


class RipoffTest(DetectedPlagiarismData, TestCase):
    def test_get_ripoff_tasks_for_user(self):
        """
        Validate that ripoff tasks for a
        given user are fetched correctly.
        """
        task_ids = get_ripoff_tasks_for_user(self.alice)
        self.assertIn(self.task.id, task_ids)


class BasicBonuspointCalculationTest(SolutionsData, TestCase):
    """Test basic functionality behind bonus point calculation."""

    def test_calculate_grades(self):
        """
        Verify that grades are computed correctly
        according to a given grading function.
        """
        def preferred_grading(user):
            if user == self.alice:
                return 1000
            return 0
        for row in calculate_grades([self.alice, self.bob], preferred_grading):
            if row[2] == self.alice.username:
                self.assertEqual(row[-1], 1000)
            if row[2] == self.bob.username:
                self.assertEqual(row[-1], 0)

    def test_points_for_completed_tasks(self):
        """
        Verify that bonus points are awarded to
        legitimate solutions.
        """
        points_for_alice = points_for_completed_tasks(
            self.category.name,
            datetime(1970, 1, 1),
            10
        )(self.alice)
        self.assertEqual(points_for_alice, 1)

    def test_no_points_for_completed_tasks(self):
        """
        Verify that the maximum bonus point
        amount is taken into account.
        """
        points_for_alice = points_for_completed_tasks(
            self.category.name,
            datetime(1970, 1, 1),
            0
        )(self.alice)
        self.assertEqual(points_for_alice, 0)

    def test_filter_zeroes(self):
        """
        Verify that zeroes are filtered in case the
        --zeroes argument is not passed to the
        management command.
        """
        mocked_grade_sequence = [
            (None, None, "Alice", None, 0),
            (None, None, "Bob", None, 1),
            (None, None, "Charles", None, -1),
        ]
        filtered_grade_sequence = list(filter_zeroes(mocked_grade_sequence))
        self.assertNotIn((None, None, "Alice", None, 0), filtered_grade_sequence)
        self.assertEqual(len(filtered_grade_sequence), 2)


class BonusPointsExportTest(SolutionsData, TestCase):
    def test_export_bonus_points(self):
        """Validate that bonus points are exported correctly."""
        stdout, file_contents, path = export_bonuspoints(
            self.task.category.name, datetime(1970, 1, 1)
        )

        self.assertIn("Successfully created {}".format(path), stdout)
        self.assertEqual(len(file_contents), 1)

        rows = "".join(file_contents)

        self.assertIn("alice", rows)
        self.assertIn("alice@example.org", rows)
        self.assertIn("1", rows, "The user alice should get 1 bonus point")
        self.assertNotIn("0", rows, "Users with 0 bonus points should be excluded")
        self.assertNotIn("2", rows, "No user should get 2 bonus points")

    def test_export_bonus_points_with_zeroes(self):
        """
        Validate that it is possible to include users without
        achieved bonuspoints in the bonuspoints export.
        """
        stdout, file_contents, path = export_bonuspoints(
            self.task.category.name, datetime(1970, 1, 1), zeroes=True
        )

        self.assertIn("Successfully created {}".format(path), stdout)
        self.assertEqual(len(file_contents), 2)

        rows = "".join(file_contents)

        self.assertIn("alice", rows)
        self.assertIn("alice@example.org", rows)
        self.assertIn("bob", rows)
        self.assertIn("bob@example.org", rows)
        self.assertIn("1", rows, "The user alice should get 1 bonus point")
        self.assertIn("0", rows, "The user bob should get no bonus points")
        self.assertNotIn("2", rows, "No user should get 2 bonus points")


class PlagiarismBonusPointsExportTest(DetectedPlagiarismData, TestCase):
    def test_export_with_detected_plagiarisms(self):
        """
        Validate that solutions with detected plagiarisms are
        suppressed during bonus points calculation.
        """
        stdout, file_contents, path = export_bonuspoints(
            self.task.category.name, datetime(1970, 1, 1)
        )

        self.assertIn("Successfully created {}".format(path), stdout)
        self.assertEqual(len(file_contents), 0)

        merged_file_contents = "".join(file_contents)

        self.assertNotIn("alice", merged_file_contents)
        self.assertNotIn("bob", merged_file_contents)


class PlagiarismVetoBonusPointsExportTest(PlagiarismTestData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.detected_plagiarism_alice_with_veto = DetectedPlagiarism.objects.create(
            test=cls.plagiarism_test,
            veto=True,
            solution=cls.passed_solution_alice,
        )
        cls.detected_plagiarism_bob_with_veto = DetectedPlagiarism.objects.create(
            test=cls.plagiarism_test,
            veto=True,
            solution=cls.passed_solution_bob,
        )

    def test_export_with_active_veto(self):
        """
        Validate that solutions with detected plagiarisms are
        not suppressed if they contain an active veto.
        """
        stdout, file_contents, path = export_bonuspoints(
            self.task.category.name, datetime(1970, 1, 1)
        )

        self.assertIn("Successfully created {}".format(path), stdout)
        self.assertEqual(len(file_contents), 2)

        rows = "".join(file_contents)

        self.assertIn("alice", rows)
        self.assertIn("alice@example.org", rows)
        self.assertIn("bob", rows)
        self.assertIn("bob@example.org", rows)
        self.assertIn("1", rows, "Each user should get 1 bonus point")
        self.assertNotIn("0", rows, "No user should get 0 bonus points")
        self.assertNotIn("2", rows, "No user should get 2 bonus points")


class BonusPointsExportTimingTest(SimpleAccountsData, SimpleTaskData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.passed_solution_1 = Solution.objects.create(
            author=cls.alice,
            task=cls.task,
            passed=True,
        )
        cls.passed_solution_2 = Solution.objects.create(
            author=cls.alice,
            task=cls.task,
            passed=True,
        )

    def test_export_bonus_points_most_recent_solution(self):
        """
        Validate that only the most recent passed solution
        is taken into account for bonus points calculation.
        """
        stdout, file_contents, path = export_bonuspoints(
            self.task.category.name, datetime.now()
        )

        self.assertIn("Successfully created {}".format(path), stdout)
        self.assertEqual(len(file_contents), 1)

        merged_file_contents = "".join(file_contents)

        self.assertIn("alice", merged_file_contents)

    def test_export_bonus_points_future_start_date(self):
        """
        Validate that start_date is taken into account for
        bonus points calculation.
        """
        stdout, file_contents, path = export_bonuspoints(
            self.task.category.name, datetime.now() + timedelta(days=1337)
        )

        self.assertIn("Successfully created {}".format(path), stdout)
        self.assertEqual(len(file_contents), 0)

        merged_file_contents = "".join(file_contents)

        self.assertNotIn("alice", merged_file_contents)


class BonusPointsExportPlagiarismTimingTest(
    PassedSolutionsData, TemporaryMediaRootTestCase
):
    def test_use_only_most_recent_plagiarism_test(self):
        """
        Validate that only the most recent plagiarism test
        is used for bonuspoints calculation.
        """

        stdout, file_contents, path = export_bonuspoints(
            self.published_task1.category.name, datetime.now()
        )
        rows = "".join(file_contents)

        self.assertIn("alice", rows)
        self.assertIn("bob", rows)

        test = PlagiarismTest.objects.create()
        DetectedPlagiarism.objects.create(test=test, solution=self.passed_solution_bob)

        stdout, file_contents, path = export_bonuspoints(
            self.published_task1.category.name, datetime.now()
        )
        rows = "".join(file_contents)

        self.assertIn("alice", rows)
        self.assertNotIn("bob", rows, "Bob should get no bonus for his plagiated solution!")
