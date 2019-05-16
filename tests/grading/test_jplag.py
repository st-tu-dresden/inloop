import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory, mkdtemp

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings, tag

from inloop.grading.copypasta import jplag_check
from inloop.solutions.models import SolutionFile
from inloop.tasks.models import Task

from tests.grading.mixins import PlagiatedSolutionsData
from tests.solutions.mixins import FailedSolutionsData

directory = os.path.dirname(os.path.realpath(__file__))

with open("{}/samples/Fibonacci.java".format(directory), "r") as f:
    FIBONACCI = f.read()

TEST_MEDIA_ROOT = mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class TemporaryMediaRootTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not os.path.isdir(TEST_MEDIA_ROOT):
            os.makedirs(TEST_MEDIA_ROOT)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_MEDIA_ROOT)
        super().tearDownClass()


@tag("slow")
class JPlagCheckTest(PlagiatedSolutionsData, TemporaryMediaRootTestCase):
    def setUp(self):
        super().setUp()
        self.plagiated_solution_file_bob = SolutionFile.objects.create(
            solution=self.passed_solution_bob,
            file=SimpleUploadedFile('FibonacciBob.java', FIBONACCI.encode())
        )
        self.plagiated_solution_file_alice = SolutionFile.objects.create(
            solution=self.passed_solution_alice,
            file=SimpleUploadedFile('FibonacciAlice.java', FIBONACCI.encode())
        )

    def test_jplag_check_with_resultdir(self):
        """JPlag check should return the right results when given a result_dir."""
        with TemporaryDirectory() as path:
            output = jplag_check(
                users=[self.alice, self.bob],
                tasks=[self.task],
                min_similarity=100,
                result_dir=Path(path).joinpath("jplag")
            )
        self.assertIn(self.passed_solution_bob, output)
        self.assertIn(self.passed_solution_alice, output)

    def test_jplag_check_without_resultdir(self):
        """JPlag check should return the right results also without result_dir."""
        output = jplag_check(
            users=[self.alice, self.bob],
            tasks=[self.task],
            min_similarity=100,
        )
        self.assertIn(self.passed_solution_bob, output)
        self.assertIn(self.passed_solution_alice, output)

    def test_specific_users(self):
        """Verify that only the given users are checked."""
        output = jplag_check(
            users=[self.alice],
            tasks=[self.task],
            min_similarity=100,
        )
        self.assertNotIn(self.passed_solution_bob, output)
        self.assertNotIn(self.passed_solution_alice, output)

    def test_specific_tasks(self):
        """Verify that only the given tasks are checked."""
        task_without_solutions = Task.objects.create(
            pubdate="2000-01-01 00:00Z",
            category_id=123456,
            title="Task without solutions",
            system_name="task-without-solutions"
        )
        output = jplag_check(
            users=[self.alice, self.bob],
            tasks=[task_without_solutions],
            min_similarity=100,
        )
        self.assertNotIn(self.passed_solution_bob, output)
        self.assertNotIn(self.passed_solution_alice, output)
        task_without_solutions.delete()


@tag("slow")
class JPlagFailedSolutionDetectionTest(FailedSolutionsData, TemporaryMediaRootTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.solution_file_bob = SolutionFile.objects.create(
            solution=cls.failed_solution_bob,
            file=SimpleUploadedFile('FibonacciBob.java', FIBONACCI.encode())
        )
        cls.solution_file_alice = SolutionFile.objects.create(
            solution=cls.failed_solution_alice,
            file=SimpleUploadedFile('FibonacciAlice.java', FIBONACCI.encode())
        )

    def test_failed_solution_detection(self):
        """Validate that failed solutions are not taken into account."""
        with TemporaryDirectory() as path:
            output = jplag_check(
                users=[self.alice, self.bob],
                tasks=[self.published_task1],
                min_similarity=1,
                result_dir=Path(path).joinpath("jplag")
            )
        self.assertNotIn(self.failed_solution_bob, output)
        self.assertNotIn(self.failed_solution_alice, output)
