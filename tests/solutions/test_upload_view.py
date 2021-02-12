import os
import shutil
from pathlib import Path
from tempfile import mkdtemp
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings, tag
from django.urls import reverse
from django.utils.html import escape

from constance.test import override_config

from inloop.accounts.forms import User
from inloop.solutions.models import Solution, SolutionFile
from inloop.tasks.models import Category, Task
from inloop.testrunner.models import TestOutput, TestResult

from tests.solutions.mixins import SolutionsData

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
class SolutionUploadTest(SolutionsData, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        self.assertTrue(self.client.login(username="bob", password="secret"))
        self.url = reverse("solutions:upload", kwargs={"slug": self.task.slug})

    def test_solution_upload_without_files(self):
        num_solutions = Solution.objects.count()
        response = self.client.post(self.url, follow=True)
        self.assertEqual(Solution.objects.count(), num_solutions)
        self.assertRedirects(response, self.url)
        self.assertContains(response, escape("You haven't uploaded any files"))

    @override_config(ALLOWED_FILENAME_EXTENSIONS=".py, .java")
    def test_upload_with_invalid_filenames(self):
        num_solutions = Solution.objects.count()
        samples = [
            SimpleUploadedFile("valid.py", b"# test"),
            SimpleUploadedFile("Valid.java", b"/* test */"),
            SimpleUploadedFile("invalid.txt", b"test"),
        ]
        response = self.client.post(self.url, data={"uploads": samples}, follow=True)
        self.assertEqual(Solution.objects.count(), num_solutions)
        self.assertRedirects(response, self.url)
        self.assertContains(response, "One or more files contain disallowed filename extensions.")

    def test_solution_upload_with_multiple_files(self):
        num_solutions = Solution.objects.count()
        samples = [
            SimpleUploadedFile("Fibonacci1.java", b"class Fibonacci1 {}"),
            SimpleUploadedFile("Fibonacci2.java", b"class Fibonacci2 {}"),
        ]
        with patch("inloop.solutions.models.solution_submitted") as mocked_signal:
            response = self.client.post(self.url, data={"uploads": samples}, follow=True)
        mocked_signal.send.assert_called_once()
        self.assertEqual(Solution.objects.count(), num_solutions + 1)
        self.assertContains(response, "Your solution has been submitted to the checker.")
        media_files = sorted(file.name for file in Path(TEST_MEDIA_ROOT).glob("**/*.java"))
        self.assertEqual(media_files, ["Fibonacci1.java", "Fibonacci2.java"])

    def test_integrity_error_is_handled(self):
        samples = [SimpleUploadedFile("Foo.java", b"public class Foo {}")]
        num_solutions = Solution.objects.count()
        with patch("inloop.solutions.models.Solution.get_next_scoped_id", return_value=1):
            # mocked bogus scoped_id should force an IntegrityError
            with self.assertLogs(level="ERROR") as capture_logs:
                response = self.client.post(self.url, data={"uploads": samples}, follow=True)
        self.assertEqual(Solution.objects.count(), num_solutions)
        self.assertRedirects(response, self.url)
        self.assertContains(response, "Concurrent submission")
        self.assertIn("db constraint violation", capture_logs.output[0])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_MEDIA_ROOT)
        super().tearDownClass()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class SolutionDetailViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not os.path.isdir(TEST_MEDIA_ROOT):
            os.makedirs(TEST_MEDIA_ROOT)

    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(id=1337, name="Category 1")
        cls.task = Task.objects.create(
            pubdate="2000-01-01 00:00Z", category=cls.category, title="Fibonacci", slug="task"
        )
        cls.bob = User.objects.create_user(
            username="bob", email="bob@example.org", password="secret"
        )
        cls.solution = Solution.objects.create(author=cls.bob, task=cls.task, passed=True)
        cls.solution_file = SolutionFile.objects.create(
            solution=cls.solution, file=SimpleUploadedFile("Fibonacci.java", FIBONACCI.encode())
        )
        cls.test_result = TestResult.objects.create(
            solution=cls.solution,
            stdout="This is the STDOUT output.",
            stderr="This is the STDERR output.",
            return_code=0,
            time_taken=1.0,
        )
        cls.test_output = TestOutput.objects.create(result=cls.test_result, name="", output="")

    def setUp(self):
        self.assertTrue(self.client.login(username="bob", password="secret"))
        self.url = reverse(
            "solutions:detail",
            kwargs={"slug": self.task.slug, "scoped_id": self.solution.scoped_id},
        )
        super().setUp()

    def test_displayed_media(self):
        """Validate that static and dynamic media is displayed correctly."""

        response = self.client.get(self.url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Congratulations, your solution passed all tests.")
        self.assertContains(response, "Fibonacci.java")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_MEDIA_ROOT)
        super().tearDownClass()
