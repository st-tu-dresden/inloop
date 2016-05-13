from os.path import dirname, join

from inloop.tasks.docker import Checker
from inloop.tasks.models import CheckerResult, TaskSolution
from inloop.tasks.test_base import TasksTestBase


TEST_DATA = join(dirname(__file__), "tests")

with open(join(TEST_DATA, "test_success.xml"), mode="rb") as f:
    TEST_SUCCESS_RESULT = f.read()

with open(join(TEST_DATA, "test_failure.xml"), mode="rb") as f:
    TEST_FAILURE_RESULT = f.read()


class CheckerTests(TasksTestBase):
    def setUp(self):
        super().setUp()
        self.ts = self.create_solution()
        self.tsf = self.create_solution_file(self.ts)
        self.c = Checker(self.ts)

    def test_correct_parse_result(self):
        self.c._parse_result(result=TEST_SUCCESS_RESULT, compiler_error=False)
        cr = CheckerResult.objects.get(solution=self.ts)
        self.assertTrue(cr.passed)
        self.assertTrue(TaskSolution.objects.get(pk=self.ts.pk).passed)
        self.assertEqual(cr.time_taken, 0.01)
        self.assertEqual(cr.stdout, TEST_SUCCESS_RESULT.decode())

    def test_failure_parse_result(self):
        self.c._parse_result(result=TEST_FAILURE_RESULT, compiler_error=False)
        cr = CheckerResult.objects.get(solution=self.ts)
        self.assertFalse(cr.passed)
        self.assertFalse(TaskSolution.objects.get(pk=self.ts.pk).passed)
        self.assertEqual(cr.time_taken, 0.01)
        self.assertEqual(cr.stdout, TEST_FAILURE_RESULT.decode())

    def test_compiler_failure_parse_result(self):
        self.c._parse_result(result="compiler trace", compiler_error=True)
        cr = CheckerResult.objects.get(solution=self.ts)
        self.assertFalse(cr.passed)
        self.assertFalse(TaskSolution.objects.get(pk=self.ts.pk).passed)
        self.assertEqual(cr.time_taken, 0.0)
        self.assertEqual(cr.stdout, "compiler trace")

    def test_empty_result_parse_result(self):
        self.c._parse_result(result="", compiler_error=False)
        cr = CheckerResult.objects.get(solution=self.ts)
        self.assertEqual(cr.stdout, "For some reason I didn't get anything.. What are you doing?")

    def test_whitespace_handling(self):
        result_crlf = TEST_SUCCESS_RESULT.replace(b"\n", b"\r\n")
        self.c._parse_result(result=result_crlf, compiler_error=False)
        cr = CheckerResult.objects.get(solution=self.ts)
        self.assertEqual(cr.stdout, result_crlf.decode())
