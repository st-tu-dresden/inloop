from datetime import datetime
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from inloop.solutions.models import Solution
from inloop.tasks.models import Task

from tests.solutions.mixins import SimpleTaskData

User = get_user_model()


@override_settings(DEBUG=True)
class GenerateSubmissionsCommandTest(SimpleTaskData, TestCase):
    @override_settings(DEBUG=False)
    def test_generate_requires_debugmode(self):
        with self.assertRaisesRegex(CommandError, "only be used in DEBUG"):
            call_command("generate_submissions", "2", "5")

    def test_params_are_validated1(self):
        with self.assertRaisesRegex(CommandError, "must be >= 1"):
            call_command("generate_submissions", "0", "5")
        with self.assertRaisesRegex(CommandError, "must be >= 1"):
            call_command("generate_submissions", "2", "0")

    def test_params_are_validated2(self):
        with self.assertRaisesRegex(CommandError, "success_rate"):
            call_command("generate_submissions", "2", "5", success_rate=-0.1)
        with self.assertRaisesRegex(CommandError, "success_rate"):
            call_command("generate_submissions", "2", "5", success_rate=1.1)

    def test_params_are_validated3(self):
        with self.assertRaisesRegex(CommandError, "num_users must be <= 10000"):
            call_command("generate_submissions", "10001", "5")

    def test_generate_requires_empty_solutions(self):
        bob = User.objects.create(username="bob", email="bob@localhost", password="secret")
        Solution.objects.create(author=bob, task=self.task, passed=False)
        with self.assertRaisesRegex(CommandError, "solutions table must be empty"):
            call_command("generate_submissions", "2", "5")

    def test_generate_requires_tasks(self):
        Task.objects.all().delete()
        with self.assertRaisesRegex(CommandError, "no tasks available"):
            call_command("generate_submissions", "2", "5")

    def test_solutions_and_users_are_generated(self):
        stdout = StringIO()
        call_command("generate_submissions", "2", "5", stdout=stdout)
        self.assertIn("created 2 user(s)", stdout.getvalue())
        self.assertIn("created 5 solution(s)", stdout.getvalue())
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Solution.objects.count(), 5)
        solutions = list(Solution.objects.all())
        for s1, s2 in zip(solutions, solutions[1:]):
            self.assertLess(s1.submission_date, s2.submission_date)

    def test_error_raised_for_unrealistic_data(self):
        with patch("inloop.solutions.management.commands.generate_submissions.timezone") as mock:
            mock.now.return_value = datetime(2014, 1, 1, tzinfo=timezone.utc)
            with self.assertRaisesRegex(CommandError, "Too many solutions requested"):
                call_command("generate_submissions", "2", "5")
        self.assertEqual(Solution.objects.count(), 0)
