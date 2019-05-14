import io
import os
import shutil
import zipfile
from tempfile import TemporaryDirectory, mkdtemp

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_text

from inloop.solutions.models import Solution, SolutionFile, create_archive
from inloop.testrunner.models import TestResult

from tests.accounts.mixins import SimpleAccountsData
from tests.tasks.mixins import TaskData


class SolutionStatusViewTest(TaskData, SimpleAccountsData, TestCase):
    def setUp(self):
        super().setUp()
        self.solution = Solution.objects.create(author=self.bob, task=self.published_task1)

    def test_pending_state(self):
        self.assertTrue(self.client.login(username="bob", password="secret"))
        response = self.client.get("/solutions/%d/solution-status" % self.solution.id)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_text(response.content),
            '{"status": "pending", "solution_id": %d}' % self.solution.id
        )

    def test_only_owner_can_access(self):
        self.assertTrue(self.client.login(username="alice", password="secret"))
        response = self.client.get("/solutions/%d/solution-status" % self.solution.id)
        self.assertEqual(response.status_code, 404)


class SolutionDetailViewRedirectTest(TaskData, SimpleAccountsData, TestCase):
    def setUp(self):
        super().setUp()
        self.solution = Solution.objects.create(author=self.bob, task=self.published_task1)

    def test_unchecked_solution_redirects(self):
        """
        Test that requesting a solution detail view redirects
        to the solution list when it was not checked yet.
        """
        self.assertTrue(self.client.login(username="bob", password="secret"))
        response = self.client.get(reverse("solutions:detail", kwargs={
            "slug": self.solution.task.slug, "scoped_id": self.solution.scoped_id
        }), follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("solutions:list", kwargs={
            "slug": self.solution.task.slug
        }))


TEST_MEDIA_ROOT = mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class SolutionDetailViewTest(TaskData, SimpleAccountsData, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not os.path.isdir(TEST_MEDIA_ROOT):
            os.makedirs(TEST_MEDIA_ROOT)

    def setUp(self):
        super().setUp()
        self.solution = Solution.objects.create(
            author=self.bob,
            task=self.published_task1,
            passed=False
        )
        self.test_result = TestResult.objects.create(
            solution=self.solution,
            stdout="STDOUT Output",
            stderr="STDERR Output",
            return_code=0,
            time_taken=0.0,
        )
        self.solution_file = SolutionFile.objects.create(
            solution=self.solution,
            file=SimpleUploadedFile("Fun.java", "public class Fun {}".encode())
        )
        self.solution.passed = self.test_result.is_success()
        self.solution.save()

    def get_view(self):
        response = self.client.get(reverse("solutions:detail", kwargs={
            "slug": self.solution.task.slug, "scoped_id": self.solution.scoped_id
        }), follow=True)
        self.assertEqual(response.status_code, 200)
        return response

    def test_overview(self):
        """Test overview tab in solution detail view."""
        self.assertTrue(self.client.login(username="bob", password="secret"))
        response = self.get_view()
        self.assertContains(response, "Congratulations, your solution passed all tests.")
        self.assertContains(response, "Fun.java")
        self.assertContains(
            response,
            "Click here to create a downloadable zip archive for this solution."
        )

    def test_files_and_archive(self):
        """Test files tab and archive creation in solution detail view."""
        self.assertTrue(self.client.login(username="bob", password="secret"))
        create_archive(self.solution)

        # Download archive
        response = self.client.get(reverse("solutions:download", kwargs={
            "solution_id": self.solution.id
        }), follow=True)
        self.assertEqual(response.status_code, 200)
        in_memory_file = io.BytesIO(response.content)
        with zipfile.ZipFile(in_memory_file) as zip_file, TemporaryDirectory() as tmp_dir:
            self.assertEqual(zip_file.namelist(), ["Fun.java"])
            self.assertIsNone(zip_file.testzip())
            zip_file.extractall(tmp_dir)
            for _, dirs, files in os.walk(tmp_dir):
                self.assertIn("Fun.java", files)
            with open(os.path.join(tmp_dir, "Fun.java"), "r") as f:
                self.assertEqual(f.read(), "public class Fun {}")

    def test_console_output(self):
        """Test console output tab in solution detail view."""
        self.assertTrue(self.client.login(username="bob", password="secret"))
        response = self.get_view()
        self.assertContains(response, "STDERR Output")
        self.assertContains(response, "STDOUT Output")

    def test_unit_tests(self):
        """test unit tests tab in solution detail view."""
        self.assertTrue(self.client.login(username="bob", password="secret"))
        response = self.get_view()
        self.assertContains(response, "Nothing to show here.")

    def tearDown(self):
        # Remove solution and associated objects
        # to ensure clean environment for each test
        self.solution.delete()
        super().tearDown()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_MEDIA_ROOT)
        super().tearDownClass()
