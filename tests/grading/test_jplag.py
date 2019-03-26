import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory, mkdtemp

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings, tag

from inloop.grading.copypasta import jplag_check
from inloop.grading.models import DetectedPlagiarism
from inloop.solutions.models import SolutionFile
from tests.solutions.mixins import SolutionsData

FIBONACCI_ITERATIVE = """
public class Fibonacci {
    // Iterative solution
    public static int fib(final int x) {
    if (x < 0) {
        throw new IllegalArgumentException("x must be greater than or equal zero");
    }

    int a = 0;
    int b = 1;

    for (int i = 0; i < x; i++) {
        int sum = a + b;
        a = b;
        b = sum;
    }

    return a;
    }

    /*
     * This comment is just here for testing purposes.
     */
}
"""

FIBONACCI_ITERATIVE_SHORTENED = """
public class Fibonacci {
    public static int fib(final int x) {
        if (x < 0) throw new IllegalArgumentException("x must be greater than or equal zero");
        int a = 0;
        int b = 1;
        for (int i = 0; i < x; i++) {
            int sum = a + b;
            a = b;
            b = sum;
        }
        return a;
    }
}
"""

FIBONACCI_RECURSIVE = """
public class Fibonacci {
    // Recursive solution
    public static int fib(int x) {
        if (x < 2) return n;
        return fibonacci(n - 1) + fibonacci(n - 2);
    }
}
"""

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
class JPlagSimplePlagiarismDetectionTest(SolutionsData, TemporaryMediaRootTestCase):
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
class JPlagMinorVariationDetectionTest(SolutionsData, TemporaryMediaRootTestCase):
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
class JPlagMajorVariationDetectionTest(SolutionsData, TemporaryMediaRootTestCase):
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
class JPlagFailedSolutionDetectionTest(SolutionsData, TemporaryMediaRootTestCase):
    def setUp(self):
        super().setUp()
        self.solution_file_bob = SolutionFile.objects.create(
            solution=self.failed_solution_bob,
            file=SimpleUploadedFile('FibonacciBob.java', FIBONACCI_ITERATIVE.encode())
        )
        self.solution_file_alice = SolutionFile.objects.create(
            solution=self.failed_solution_alice,
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
