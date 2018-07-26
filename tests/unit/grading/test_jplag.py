import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory, mkdtemp

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings, tag

from inloop.grading.copypasta import jplag_check
from inloop.solutions.models import SolutionFile

from tests.unit.grading.mixins import PlagiatedSolutionsData

FIBONACCI = """
public class Fibonacci {
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
     * This string is just here for testing purposes.
     */
}
"""

TEST_MEDIA_ROOT = mkdtemp()


@tag("slow")
@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class JPlagCheckTest(PlagiatedSolutionsData, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not os.path.isdir(TEST_MEDIA_ROOT):
            os.makedirs(TEST_MEDIA_ROOT)

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

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_MEDIA_ROOT)
        super().tearDownClass()
