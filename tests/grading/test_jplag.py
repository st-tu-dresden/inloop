import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory, mkdtemp

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings, tag

from inloop.grading.copypasta import jplag_check
from inloop.grading.models import DetectedPlagiarism
from inloop.solutions.models import SolutionFile

from tests.solutions.mixins import FailedSolutionsData, PassedSolutionsData

directory = os.path.dirname(os.path.realpath(__file__))

with open("{}/samples/FibonacciIterative.java".format(directory), "r") as f:
    FIBONACCI_ITERATIVE = f.read()

with open("{}/samples/FibonacciIterativeSlightlyChanged.java".format(directory), "r") as f:
    FIBONACCI_ITERATIVE_SLIGHTLY_CHANGED = f.read()

with open("{}/samples/FibonacciIterativeShortened.java".format(directory), "r") as f:
    FIBONACCI_ITERATIVE_SHORTENED = f.read()

with open("{}/samples/FibonacciRecursive.java".format(directory), "r") as f:
    FIBONACCI_RECURSIVE = f.read()

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
class JPlagSimplePlagiarismDetectionTest(PassedSolutionsData, TemporaryMediaRootTestCase):
    def setUp(self):
        super().setUp()
        self.plagiated_solution_file_bob = SolutionFile.objects.create(
            solution=self.passed_solution_bob,
            file=SimpleUploadedFile('FibonacciBob.java', FIBONACCI_ITERATIVE.encode())
        )
        self.plagiated_solution_file_alice = SolutionFile.objects.create(
            solution=self.passed_solution_alice,
            file=SimpleUploadedFile('FibonacciAlice.java', FIBONACCI_ITERATIVE.encode())
        )

    def test_jplag_check_with_resultdir(self):
        """JPlag check should return the right results when given a result_dir."""
        with TemporaryDirectory() as path:
            output = jplag_check(
                users=[self.alice, self.bob],
                tasks=[self.published_task1],
                min_similarity=100,
                result_dir=Path(path).joinpath("jplag")
            )
        self.assertIn(self.passed_solution_bob, output)
        self.assertIn(self.passed_solution_alice, output)

        detected_plagiarisms = DetectedPlagiarism.objects.all()
        flagged_solutions = [p.solution for p in detected_plagiarisms]
        self.assertIn(self.passed_solution_bob, flagged_solutions)
        self.assertIn(self.passed_solution_alice, flagged_solutions)

    def test_jplag_check_without_resultdir(self):
        """JPlag check should return the right results also without result_dir."""
        output = jplag_check(
            users=[self.alice, self.bob],
            tasks=[self.published_task1],
            min_similarity=100,
        )
        self.assertIn(self.passed_solution_bob, output)
        self.assertIn(self.passed_solution_alice, output)

    def test_specific_users(self):
        """Verify that only the given users are checked."""
        output = jplag_check(
            users=[self.alice],
            tasks=[self.published_task1],
            min_similarity=100,
        )
        self.assertNotIn(self.passed_solution_bob, output)
        self.assertNotIn(self.passed_solution_alice, output)

    def test_specific_tasks(self):
        """Verify that only the given tasks are checked."""
        output = jplag_check(
            users=[self.alice, self.bob],
            tasks=[self.published_task2],
            min_similarity=100,
        )
        self.assertNotIn(self.passed_solution_bob, output)
        self.assertNotIn(self.passed_solution_alice, output)


@tag("slow")
class JPlagMinorVariationDetectionTest(PassedSolutionsData, TemporaryMediaRootTestCase):
    def setUp(self):
        super().setUp()
        self.plagiated_solution_file_bob = SolutionFile.objects.create(
            solution=self.passed_solution_bob,
            file=SimpleUploadedFile('FibonacciBob.java', FIBONACCI_ITERATIVE.encode())
        )
        self.plagiated_solution_file_alice = SolutionFile.objects.create(
            solution=self.passed_solution_alice,
            file=SimpleUploadedFile('FibonacciAlice.java', FIBONACCI_ITERATIVE_SHORTENED.encode())
        )

    def test_minor_variation_detection(self):
        """Validate that minor code variations are still recognized as plagiarisms."""
        with TemporaryDirectory() as path:
            output = jplag_check(
                users=[self.alice, self.bob],
                tasks=[self.published_task1],
                min_similarity=100,
                result_dir=Path(path).joinpath("jplag")
            )
        self.assertIn(self.passed_solution_bob, output)
        self.assertIn(self.passed_solution_alice, output)


@tag("slow")
class JPlagMajorVariationDetectionTest(PassedSolutionsData, TemporaryMediaRootTestCase):
    def setUp(self):
        super().setUp()
        self.solution_file_bob = SolutionFile.objects.create(
            solution=self.passed_solution_bob,
            file=SimpleUploadedFile('FibonacciBob.java', FIBONACCI_ITERATIVE.encode())
        )
        self.solution_file_alice = SolutionFile.objects.create(
            solution=self.passed_solution_alice,
            file=SimpleUploadedFile('FibonacciAlice.java', FIBONACCI_RECURSIVE.encode())
        )

    def test_major_variation_detection(self):
        """
        Validate that major code variations are not recognized as plagiarisms.

        Since both submissions are completely distinct, they should be
        less than 1% similar, according to JPlag.
        """
        with TemporaryDirectory() as path:
            output = jplag_check(
                users=[self.alice, self.bob],
                tasks=[self.published_task1],
                min_similarity=1,
                result_dir=Path(path).joinpath("jplag")
            )
        self.assertNotIn(self.passed_solution_bob, output)
        self.assertNotIn(self.passed_solution_alice, output)


@tag("slow")
class JPlagFailedSolutionDetectionTest(FailedSolutionsData, TemporaryMediaRootTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.solution_file_bob = SolutionFile.objects.create(
            solution=cls.failed_solution_bob,
            file=SimpleUploadedFile('FibonacciBob.java', FIBONACCI_ITERATIVE.encode())
        )
        cls.solution_file_alice = SolutionFile.objects.create(
            solution=cls.failed_solution_alice,
            file=SimpleUploadedFile('FibonacciAlice.java', FIBONACCI_ITERATIVE.encode())
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
