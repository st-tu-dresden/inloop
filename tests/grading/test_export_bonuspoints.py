from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, tag

from inloop.grading.copypasta import jplag_check
from inloop.grading.management.commands import tud_export_bonuspoints_csv
from inloop.solutions.models import Solution, SolutionFile

from tests.accounts.mixins import SimpleAccountsData
from tests.grading.mixins import DetectedPlagiarismData, DetectedVetoCounteredPlagiarismData
from tests.grading.test_jplag import (FIBONACCI_ITERATIVE, FIBONACCI_ITERATIVE_SLIGHTLY_CHANGED,
                                      TemporaryMediaRootTestCase)
from tests.solutions.mixins import PassedSolutionsData, SolutionsData
from tests.tasks.mixins import TaskData


class BonusPointsTestCase(TestCase):
    def export_bonuspoints(self, category_name, date):
        """Conveniently execute the bonus points export management command."""
        stdout = StringIO()
        with TemporaryDirectory() as path:
            output_path = Path(path).joinpath("output")
            args = [category_name, date.strftime("%Y-%m-%d"), output_path]
            call_command(tud_export_bonuspoints_csv.Command(), *args, stdout=stdout)

            with open(str(output_path), "r") as f:
                return stdout.getvalue(), f.readlines(), output_path


class BonusPointsExportTest(SolutionsData, BonusPointsTestCase):
    def test_export_bonus_points(self):
        """Validate that bonus points are exported correctly."""
        stdout, file_contents, path = self.export_bonuspoints(
            self.published_task1.category.name, datetime(1970, 1, 1)
        )

        self.assertIn("Successfully created {}".format(path), stdout)
        self.assertEqual(len(file_contents), 2)

        merged_file_contents = "".join(file_contents)

        self.assertIn(",,alice,alice@example.org,,,1", merged_file_contents)
        self.assertIn(",,bob,bob@example.org,,,1", merged_file_contents)


class PlagiarismInfluencedBonusPointsExportTest(DetectedPlagiarismData, BonusPointsTestCase):
    def test_export_with_detected_plagiarisms(self):
        """
        Validate that solutions with detected plagiarisms are
        suppressed during bonus points calculation.
        """
        stdout, file_contents, path = self.export_bonuspoints(
            self.published_task1.category.name, datetime(1970, 1, 1)
        )

        self.assertIn("Successfully created {}".format(path), stdout)
        self.assertEqual(len(file_contents), 0)

        merged_file_contents = "".join(file_contents)

        self.assertNotIn("alice", merged_file_contents)
        self.assertNotIn("bob", merged_file_contents)


class PlagiarismInfluencedVetoCounteredBonusPointsExportTest(
    DetectedVetoCounteredPlagiarismData, BonusPointsTestCase
):
    def test_export_with_active_veto(self):
        """
        Validate that solutions with detected plagiarisms are
        not suppressed if they contain an active veto.
        """
        stdout, file_contents, path = self.export_bonuspoints(
            self.published_task1.category.name, datetime(1970, 1, 1)
        )

        self.assertIn("Successfully created {}".format(path), stdout)
        self.assertEqual(len(file_contents), 2)

        merged_file_contents = "".join(file_contents)

        self.assertIn(",,alice,alice@example.org,,,1", merged_file_contents)
        self.assertIn(",,bob,bob@example.org,,,1", merged_file_contents)


class BonusPointsExportTimingTest(SimpleAccountsData, TaskData, BonusPointsTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.passed_solution_1 = Solution.objects.create(
            author=cls.alice,
            task=cls.published_task1,
            passed=True,
        )
        cls.passed_solution_2 = Solution.objects.create(
            author=cls.alice,
            task=cls.published_task1,
            passed=True,
        )

    def test_export_bonus_points_most_recent_solution(self):
        """
        Validate that only the most recent passed solution
        is taken into account for bonus points calculation.
        """
        stdout, file_contents, path = self.export_bonuspoints(
            self.published_task1.category.name, datetime.now()
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
        stdout, file_contents, path = self.export_bonuspoints(
            self.published_task1.category.name, datetime.now() + timedelta(days=1337)
        )

        self.assertIn("Successfully created {}".format(path), stdout)
        self.assertEqual(len(file_contents), 0)

        merged_file_contents = "".join(file_contents)

        self.assertNotIn("alice", merged_file_contents)


@tag("slow")
class BonusPointsExportPlagiarismTimingTest(
    PassedSolutionsData, TemporaryMediaRootTestCase, BonusPointsTestCase
):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.plagiated_solution_file_bob = SolutionFile.objects.create(
            solution=cls.passed_solution_bob,
            file=SimpleUploadedFile("Test.java", FIBONACCI_ITERATIVE.encode())
        )
        cls.plagiated_solution_file_alice = SolutionFile.objects.create(
            solution=cls.passed_solution_alice,
            file=SimpleUploadedFile("Test.java", FIBONACCI_ITERATIVE_SLIGHTLY_CHANGED.encode())
        )

    def test_use_only_most_recent_plagiarism_test(self):
        """Validate that only the most recent plagiarism test is used."""
        with TemporaryDirectory() as path:
            output = jplag_check(
                users=[self.alice, self.bob],
                tasks=[self.passed_solution_bob.task],
                min_similarity=100,
                result_dir=Path(path).joinpath("jplag")
            )
            # Output should be empty
            self.assertFalse(output)

        stdout, file_contents, path = self.export_bonuspoints(
            self.passed_solution_bob.task.category.name, datetime.now()
        )

        self.assertIn("Successfully created {}".format(path), stdout)
        self.assertEqual(len(file_contents), 2)

        merged_file_contents = "".join(file_contents)

        self.assertIn("alice", merged_file_contents)
        self.assertIn("bob", merged_file_contents)

        with TemporaryDirectory() as path:
            output = jplag_check(
                users=[self.alice, self.bob],
                tasks=[self.passed_solution_bob.task],
                min_similarity=1,
                result_dir=Path(path).joinpath("jplag")
            )
            # Output should detect plagiarisms
            self.assertTrue(output)

        stdout, file_contents, path = self.export_bonuspoints(
            self.passed_solution_bob.task.category.name, datetime.now()
        )

        self.assertIn("Successfully created {}".format(path), stdout)
        self.assertEqual(len(file_contents), 0)

        merged_file_contents = "".join(file_contents)

        self.assertNotIn("alice", merged_file_contents)
        self.assertNotIn("bob", merged_file_contents)
