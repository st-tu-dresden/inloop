import os
import shutil
import tempfile
from tempfile import TemporaryDirectory

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

TEST_MEDIA_ROOT = tempfile.mkdtemp()


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

    def test_jplag(self):
        with TemporaryDirectory() as path:
            check = jplag_check(
                min_similarity=100,
                users=[self.alice, self.bob],
                tasks=[self.task],
                result_dir=path
            )
        self.assertTrue(self.passed_solution_bob in check)
        self.assertTrue(self.passed_solution_alice in check)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_MEDIA_ROOT)
        super().tearDownClass()
