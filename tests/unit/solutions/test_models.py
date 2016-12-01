# flake8: noqa
from unittest import skip

from django.test import TestCase


# XXX: this beast needs to split up
@skip
class HugeSteamingPileOfCrapMonolithModelTest(TestCase):
    def setUp(self):
        super().setUp()
        self.solution = self.create_solution()
        self.solutionfile = self.create_solution_file(solution=self.solution)

    def create_mock_checker(self, return_value):
        checker = mock.MagicMock()
        checker.check_task = mock.MagicMock(return_value=return_value)
        return checker

    def test_precondition(self):
        """Verify there are no results before calling TaskSolution.do_check()."""
        self.assertEqual(self.solution.checkerresult_set.count(), 0)
        self.assertFalse(self.solution.passed)

    def test_checkerresult_saved(self):
        """Test if the CheckerResult is saved with the right values."""
        self.solution.do_check(self.create_mock_checker(
            ResultTuple(0, "OUT", "ERR", 1.2, dict())
        ))

        result_set = self.solution.checkerresult_set
        self.assertEqual(result_set.count(), 1)

        result = result_set.first()
        self.assertEqual(result.stdout, "OUT")
        self.assertEqual(result.stderr, "ERR")
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.time_taken, 1.2)

        self.assertTrue(self.solution.passed)

    def test_checkeroutputs_saved(self):
        """Test if CheckerOutputs are saved."""
        self.solution.do_check(self.create_mock_checker(
            ResultTuple(1, "OUT", "ERR", 0.2, {"test.txt": "content", "test2.txt": "content2"})
        ))

        output_set = self.solution.checkerresult_set.first().checkeroutput_set
        self.assertEqual(output_set.count(), 2)
        self.assertEqual(output_set.filter(name="test.txt").count(), 1)
        self.assertEqual(output_set.filter(name="test2.txt").count(), 1)
        self.assertEqual(output_set.filter(name="test.txt").first().output, "content")
        self.assertEqual(output_set.filter(name="test2.txt").first().output, "content2")

    def test_failure_means_not_passed(self):
        """Test if non-zero rc marks the solution as not passed."""
        self.solution.do_check(self.create_mock_checker(
            ResultTuple(1, "OUT", "ERR", 0.2, dict())
        ))
        results = self.solution.checkerresult_set.all()
        self.assertEqual(results.count(), 1)
        self.assertFalse(self.solution.passed)

    def test_solution_input_is_used(self):
        """Test if TaskSolutionFiles are passed to the Checker."""
        checker = self.create_mock_checker(
            ResultTuple(0, "OUT", "ERR", 1.2, dict())
        )
        self.solution.do_check(checker)
        checker.check_task.assert_called_with(
            self.task_defaults["name"],
            path.dirname(self.solutionfile.file.path)
        )

    def test_get_upload_path(self):
        solution = self.create_solution()
        tsf = self.create_solution_file(solution=solution)
        self.assertRegex(
            models.get_upload_path(tsf, tsf.filename),
            (r"solutions/chuck_norris/published-task/"
             "[\d]{4}/[\d]{2}/[\d]{2}/[\d]{2}_[\d]{1,2}_[\d]+/HelloWorld.java")
        )

    def test_solution_default_status(self):
        solution = self.create_solution()
        self.assertFalse(solution.checkerresult_set.exists())
        self.assertEqual(solution.status(), "pending")

    def test_solution_lost_status(self):
        solution = self.create_solution()
        mocked_time = timezone.now() + timezone.timedelta(minutes=6)
        with mock.patch("django.utils.timezone.now", return_value=mocked_time):
            self.assertFalse(solution.checkerresult_set.exists())
            self.assertEqual(solution.status(), "lost")

    def test_solution_failure_status(self):
        solution = self.create_solution()
        solution.checkerresult_set.add(CheckerResult(), bulk=False)
        self.assertEqual(solution.status(), "failure")
