from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import TestCase

from inloop.grading.management.commands import tud_export_bonuspoints_csv

from tests.solutions.mixins import SolutionsData


class BonuspointsExportTest(SolutionsData, TestCase):
    def test_export_bonuspoints(self):
        stdout = StringIO()
        with TemporaryDirectory() as path:
            output_path = Path(path).joinpath("output")
            args = [
                self.published_task1.category.name,
                datetime(1970, 1, 1).strftime("%Y-%m-%d"),
                output_path
            ]
            call_command(tud_export_bonuspoints_csv.Command(), *args, stdout=stdout)

            with open(output_path, "r") as f:
                file_contents = f.readlines()

        self.assertIn("Successfully created {}".format(output_path), stdout.getvalue())
        self.assertEqual(len(file_contents), 2)

        self.assertIn(",,alice,alice@example.org,,,1\n", file_contents)
        self.assertIn(",,bob,bob@example.org,,,1\n", file_contents)

    def test_export_bonuspoints_future_start_date(self):
        stdout = StringIO()
        with TemporaryDirectory() as path:
            output_path = Path(path).joinpath("output")
            start_date = datetime.now() + timedelta(days=1337)
            args = [
                self.published_task1.category.name,
                start_date.strftime("%Y-%m-%d"),
                output_path
            ]
            call_command(tud_export_bonuspoints_csv.Command(), *args, stdout=stdout)

            with open(output_path, "r") as f:
                file_contents = f.readlines()

        self.assertIn("Successfully created {}".format(output_path), stdout.getvalue())
        self.assertEqual(len(file_contents), 0)

        self.assertNotIn(",,alice,alice@example.org,,,1\n", file_contents)
        self.assertNotIn(",,bob,bob@example.org,,,1\n", file_contents)
