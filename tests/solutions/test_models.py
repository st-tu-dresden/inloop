import os
import shutil
from tempfile import TemporaryDirectory, mkdtemp
from unittest.mock import Mock
from zipfile import ZipFile, is_zipfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone

from inloop.solutions.models import (
    Solution,
    SolutionFile,
    create_archive,
    get_archive_upload_path,
    get_upload_path,
)

from tests.accounts.mixins import SimpleAccountsData
from tests.solutions.mixins import SimpleTaskData, SolutionsData


class SolutionsModelTest(SolutionsData, TestCase):
    def test_precondition(self):
        """Verify there are no results before checking."""
        self.assertEqual(self.failed_solution.testresult_set.count(), 0)
        self.assertFalse(self.failed_solution.passed)

    def test_solution_default_status(self):
        """Verify that the default status of a solution is pending."""

        # Both failed_solution and passed_solution were not checked yet
        # so their status should be pending
        self.assertEqual(self.failed_solution.status(), 'pending')
        self.assertEqual(self.passed_solution.status(), 'pending')

    def test_solution_lost_status(self):
        """
        Verify that a solution is lost when it was not processed
        in a reasonable amount of time.
        """
        delayed_solution = Solution.objects.create(
            author=self.bob,
            task=self.task,
            passed=False,
        )
        # Simulate that the solution was submitted one hour ago.
        # The solution should therefore be marked as lost.
        mocked_time = timezone.now() - timezone.timedelta(hours=1)
        delayed_solution.submission_date = mocked_time
        self.assertEqual(delayed_solution.status(), 'lost')


class SolutionsFileUploadTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Create a mock solution to check its
        # computed upload path
        cls.mock = Mock()
        cls.mock.solution.submission_date.year = '1970'
        cls.mock.solution.task.slug = 'here-be-dragons'
        cls.mock.solution.author = 'Mr. Mustermann'
        cls.mock.solution.id = '123456'

    def test_get_upload_path(self):
        """Test the upload path for solution files."""

        upload_path = get_upload_path(self.mock, 'Fibonacci.java')
        self.assertTrue(upload_path.startswith('solutions'))
        self.assertTrue(upload_path.endswith('Fibonacci.java'))

        tokens = upload_path.split('/')
        for token in ['1970', 'here-be-dragons', '123456']:
            self.assertTrue(token in tokens)

    def test_get_archive_upload_path(self):
        """
        Test the upload path for archives
        associated with a particular solution.
        """
        upload_path = get_archive_upload_path(
            self.mock.solution, 'Fibonacci.zip'
        )

        self.assertTrue(upload_path.startswith('archives'))
        self.assertTrue(upload_path.endswith('Fibonacci.zip'))


JAVA_EXAMPLE_1 = """
public class Example {
    //...
}
""".encode()

JAVA_EXAMPLE_2 = ''.encode()


TEST_MEDIA_ROOT = mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class SolutionSignalsTest(SimpleAccountsData, SimpleTaskData, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not os.path.isdir(TEST_MEDIA_ROOT):
            os.makedirs(TEST_MEDIA_ROOT)

    def setUp(self):
        super().setUp()
        self.solution = Solution.objects.create(
            author=self.alice,
            task=self.task,
            passed=True,
        )
        self.solution_file = SolutionFile.objects.create(
            solution=self.solution,
            file=SimpleUploadedFile('Example1.java', JAVA_EXAMPLE_1)
        )

    def test_archive_post_delete(self):
        """
        Validate that solution archives are deleted correctly
        after the corresponding solution was deleted.
        """
        create_archive(self.solution)
        archive_path = self.solution.archive.path
        self.assertTrue(os.path.isfile(archive_path))
        self.solution.delete()
        self.assertFalse(os.path.isfile(archive_path))

    def test_solution_file_post_delete(self):
        """
        Validate that solution files are deleted correctly
        after the corresponding solution was deleted.
        """
        solution_file_path = self.solution_file.absolute_path
        self.assertTrue(solution_file_path.is_file())
        self.solution.delete()
        self.assertFalse(solution_file_path.is_file())

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_MEDIA_ROOT)
        super().tearDownClass()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class SolutionsModelArchiveTest(SolutionsData, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not os.path.isdir(TEST_MEDIA_ROOT):
            os.makedirs(TEST_MEDIA_ROOT)

    def setUp(self):
        super().setUp()
        self.solution_file_passed_1 = SolutionFile.objects.create(
            solution=self.passed_solution,
            file=SimpleUploadedFile('Example1.java', JAVA_EXAMPLE_1)
        )
        self.solution_file_passed_2 = SolutionFile.objects.create(
            solution=self.passed_solution,
            file=SimpleUploadedFile('Example2.java', JAVA_EXAMPLE_2)
        )
        self.solution_file_failed_1 = SolutionFile.objects.create(
            solution=self.failed_solution,
            file=SimpleUploadedFile('Example1.java', JAVA_EXAMPLE_1)
        )
        self.solution_file_failed_2 = SolutionFile.objects.create(
            solution=self.failed_solution,
            file=SimpleUploadedFile('Example2.java', JAVA_EXAMPLE_2)
        )

    def test_archive_creation(self):
        """Test archive creation for solutions."""
        for solution in [self.passed_solution, self.failed_solution]:
            self.assertFalse(solution.archive)

            create_archive(solution)

            self.assertTrue(solution.archive)
            self.assertTrue(is_zipfile(solution.archive.path))
            with ZipFile(solution.archive.path) as zipfile:
                self.assertIn('Example1.java', zipfile.namelist())
                self.assertIn('Example2.java', zipfile.namelist())

                with zipfile.open('Example1.java') as stream:
                    self.assertEqual(stream.read(), JAVA_EXAMPLE_1)
                with zipfile.open('Example2.java') as stream:
                    self.assertEqual(stream.read(), JAVA_EXAMPLE_2)

                with TemporaryDirectory() as tmpdir:
                    # Test extraction to expose erroneous packaging
                    zipfile.extractall(tmpdir)
                    for _, dirs, files in os.walk(tmpdir):
                        self.assertIn('Example1.java', files)
                        self.assertIn('Example2.java', files)
                        self.assertEqual(2, len(files))

                        # The inherited folder structure should be flat
                        self.assertFalse(dirs)

                self.assertIsNone(zipfile.testzip())

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_MEDIA_ROOT)
        super().tearDownClass()
