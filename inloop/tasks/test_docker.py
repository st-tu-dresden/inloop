from os import remove
from os.path import dirname, join
from shutil import copy, which

from django.test import TestCase

from inloop.tasks.docker import Checker
from inloop.tasks.models import CheckerResult, TaskSolution
from inloop.tasks.tests import (create_test_user, create_task_category, create_test_task,
                                create_test_task_solution, create_test_task_solution_file)
from inloop.tasks.tests import (TEST_IMAGE_PATH, MEDIA_IMAGE_PATH,
                                TEST_CLASS_PATH, MEDIA_CLASS_PATH)

TEST_DATA = join(dirname(__file__), "tests")

with open(join(TEST_DATA, "test_success.xml"), mode="rb") as f:
    TEST_SUCCESS_RESULT = f.read()

with open(join(TEST_DATA, "test_failure.xml"), mode="rb") as f:
    TEST_FAILURE_RESULT = f.read()


class CheckerTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        copy(TEST_IMAGE_PATH, MEDIA_IMAGE_PATH)
        copy(TEST_CLASS_PATH, MEDIA_CLASS_PATH)

    @classmethod
    def tearDownClass(cls):
        remove(MEDIA_IMAGE_PATH)
        remove(MEDIA_CLASS_PATH)
        super().tearDownClass()

    def setUp(self):
        self.user = create_test_user()
        self.cat = create_task_category("Basic", MEDIA_IMAGE_PATH)
        self.task = create_test_task(author=self.user, category=self.cat, active=True)
        self.ts = create_test_task_solution(author=self.user, task=self.task)
        self.tsf = create_test_task_solution_file(solution=self.ts, contentpath=MEDIA_CLASS_PATH)
        self.c = Checker(self.ts)

    def tearDown(self):
        remove(self.cat.image.path)

    def test_docker_present_on_system(self):
        self.assertIsNotNone(which("docker"), "Docker is not available on your system.")

    def test_generate_container_name_format(self):
        self.assertRegex(
            self.c._generate_container_name(),
            "-".join([self.user.username, self.task.slug, "[\\w]{21}"])
        )

    def test_correct_parse_result(self):
        self.c._parse_result(result=TEST_SUCCESS_RESULT, compiler_error=False)
        cr = CheckerResult.objects.get(solution=self.ts)
        self.assertTrue(cr.passed)
        self.assertTrue(TaskSolution.objects.get(pk=self.ts.pk).passed)
        self.assertEqual(cr.time_taken, 0.01)
        self.assertEqual(cr.result, TEST_SUCCESS_RESULT.decode())

    def test_failure_parse_result(self):
        self.c._parse_result(result=TEST_FAILURE_RESULT, compiler_error=False)
        cr = CheckerResult.objects.get(solution=self.ts)
        self.assertFalse(cr.passed)
        self.assertFalse(TaskSolution.objects.get(pk=self.ts.pk).passed)
        self.assertEqual(cr.time_taken, 0.01)
        self.assertEqual(cr.result, TEST_FAILURE_RESULT.decode())

    def test_compiler_failure_parse_result(self):
        self.c._parse_result(result="compiler trace", compiler_error=True)
        cr = CheckerResult.objects.get(solution=self.ts)
        self.assertFalse(cr.passed)
        self.assertFalse(TaskSolution.objects.get(pk=self.ts.pk).passed)
        self.assertEqual(cr.time_taken, 0.0)
        self.assertEqual(cr.result, "compiler trace")

    def test_empty_result_parse_result(self):
        self.c._parse_result(result="", compiler_error=False)
        cr = CheckerResult.objects.get(solution=self.ts)
        self.assertEqual(cr.result, "For some reason I didn't get anything.. What are you doing?")
