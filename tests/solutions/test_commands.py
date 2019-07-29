from datetime import datetime
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, tag
from django.utils.timezone import make_aware

from inloop.solutions.management.commands.generate_submissions import Command
from inloop.solutions.models import Solution
from inloop.tasks.models import Task

from tests.solutions.mixins import SimpleTaskData

User = get_user_model()

DATEFORMAT = Command.dateformat
START_DATE_STR = "01.01.1970"
END_DATE_STR = "31.12.2018"


@tag("slow")
class GenerateSubmissionsTest(SimpleTaskData, TestCase):
    def test_command(self):
        """Verify that submissions can be generated correctly."""
        opts = {
            "start_date": START_DATE_STR,
            "end_date": END_DATE_STR,
            "solutions_number": 10,
            "users_number": 10,
            "force": True,
            "stdout": StringIO()
        }
        call_command("generate_submissions", **opts)

        self.assertEqual(Solution.objects.all().count(), 10)
        self.assertEqual(User.objects.all().count(), 10)

        start_date = make_aware(datetime.strptime(START_DATE_STR, DATEFORMAT))
        end_date = make_aware(datetime.strptime(END_DATE_STR, DATEFORMAT))

        for solution in Solution.objects.all():
            self.assertTrue(solution.submission_date > start_date)
            self.assertTrue(solution.submission_date < end_date)

    def test_force(self):
        """Test the force flag of the management command."""
        opts = {
            "start_date": START_DATE_STR,
            "end_date": END_DATE_STR,
            "force": True,
            "stdout": StringIO()
        }
        call_command("generate_submissions", **opts)
        self.assertNotEqual(Solution.objects.all().count(), 0)
        self.assertNotEqual(User.objects.all().count(), 0)

    def test_prompt(self):
        """
        Verify that the user has to confirm the
        generation of submissions first.
        """
        opts = {
            "start_date": START_DATE_STR,
            "end_date": END_DATE_STR,
            "stdout": StringIO()
        }
        func_to_patch = "inloop.solutions.management.commands.generate_submissions.input"
        with patch(func_to_patch, return_value="n"):
            call_command("generate_submissions", **opts)
        self.assertEqual(Solution.objects.all().count(), 0)
        self.assertEqual(User.objects.all().count(), 0)

    def test_erronenous_input_dates(self):
        """Verify that the input dates are checked for validity."""
        opts = {
            "start_date": END_DATE_STR,
            "end_date": START_DATE_STR,
            "stdout": StringIO()
        }
        try:
            call_command("generate_submissions", **opts)
            self.fail("The management command should check the input dates for validity.")
        except ValueError:
            pass

    def test_silent(self):
        """Verify that command line output is only produced when needed."""
        out = StringIO()
        opts = {
            "start_date": START_DATE_STR,
            "end_date": END_DATE_STR,
            "force": True,
            "stdout": out,
            "verbosity": 0
        }
        call_command("generate_submissions", **opts)
        self.assertFalse(out.getvalue())
        opts["verbosity"] = 1
        call_command("generate_submissions", **opts)
        self.assertTrue(out.getvalue())


class EmptyDatabaseGenerateTest(TestCase):
    def test_no_task(self):
        """Verify that the command fails when there is no available task."""
        opts = {
            "start_date": START_DATE_STR,
            "end_date": END_DATE_STR,
            "force": True,
            "stdout": StringIO()
        }
        self.assertEqual(Task.objects.count(), 0)
        try:
            call_command("generate_submissions", **opts)
            self.fail("The management command should fail, when there are no tasks.")
        except ValueError:
            pass
