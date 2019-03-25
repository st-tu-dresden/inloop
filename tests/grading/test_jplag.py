import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory, mkdtemp

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings, tag

from inloop.grading.copypasta import jplag_check
from inloop.solutions.models import SolutionFile

from tests.grading.mixins import PlagiatedSolutionsData

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
class JPlagSimplePlagiarismDetectionTest(PlagiatedSolutionsData, TemporaryMediaRootTestCase):
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
                tasks=[self.task],
                min_similarity=100,
                result_dir=Path(path).joinpath("jplag")
            )
        self.assertTrue(self.passed_solution_bob in output)
        self.assertTrue(self.passed_solution_alice in output)

    def test_jplag_check_without_resultdir(self):
        """JPlag check should return the right results also without result_dir."""
        output = jplag_check(
            users=[self.alice, self.bob],
            tasks=[self.task],
            min_similarity=100,
        )
        self.assertTrue(self.passed_solution_bob in output)
        self.assertTrue(self.passed_solution_alice in output)


@tag("slow")
class JPlagPlagiarismVariationDetectionTest(PlagiatedSolutionsData, TemporaryMediaRootTestCase):
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

    def test_comment_variation_detection(self):
        """Validate that simple code variations are still recognized as plagiarisms."""
        with TemporaryDirectory() as path:
            output = jplag_check(
                users=[self.alice, self.bob],
                tasks=[self.task],
                min_similarity=100,
                result_dir=Path(path).joinpath("jplag")
            )
            print(output)
        self.assertTrue(self.passed_solution_bob in output)
        self.assertTrue(self.passed_solution_alice in output)
