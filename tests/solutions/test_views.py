import os
import shutil
from tempfile import mkdtemp

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings, tag
from django.urls import reverse
from django.utils.encoding import force_text

from inloop.solutions.models import (Checkpoint, CheckpointFile, Solution,
                                     SolutionFile, create_archive)
from inloop.tasks.models import FileTemplate
from inloop.testrunner.models import TestResult

from tests.accounts.mixins import AccountsData, SimpleAccountsData
from tests.tasks.mixins import TaskData


class SolutionStatusViewTest(TaskData, SimpleAccountsData, TestCase):
    def setUp(self):
        super().setUp()
        self.solution = Solution.objects.create(author=self.bob, task=self.published_task1)

    def test_pending_state(self):
        self.assertTrue(self.client.login(username='bob', password='secret'))
        response = self.client.get(reverse('solutions:status', kwargs={
            'id': self.solution.id
        }))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_text(response.content),
            '{"status": "pending", "solution_id": %d}' % self.solution.id
        )

    def test_only_owner_can_access(self):
        self.assertTrue(self.client.login(username='alice', password='secret'))
        response = self.client.get(reverse('solutions:status', kwargs={
            'id': self.solution.id
        }))
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
        self.assertTrue(self.client.login(username='bob', password='secret'))
        response = self.client.get(reverse('solutions:detail', kwargs={
            'slug': self.solution.task.slug, 'scoped_id': self.solution.scoped_id
        }), follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('solutions:list', kwargs={
            'slug': self.solution.task.slug
        }))


TEST_MEDIA_ROOT = mkdtemp()


@tag('slow')
@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class SolutionDetailViewTest(TaskData, AccountsData, TestCase):
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
            stdout='STDOUT Output',
            stderr='STDERR Output',
            return_code=0,
            time_taken=0.0,
        )
        self.solution_file = SolutionFile.objects.create(
            solution=self.solution,
            file=SimpleUploadedFile('Fun.java', 'public class Fun {}'.encode())
        )
        self.solution.passed = self.test_result.is_success()
        self.solution.save()

    def get_view(self):
        response = self.client.get(reverse('solutions:detail', kwargs={
            'slug': self.solution.task.slug, 'scoped_id': self.solution.scoped_id
        }), follow=True)
        self.assertEqual(response.status_code, 200)
        return response

    def test_overview(self):
        """Test overview tab in solution detail view."""
        self.assertTrue(self.client.login(username='bob', password='secret'))
        response = self.get_view()
        self.assertContains(response, 'Congratulations, your solution passed all tests.')
        self.assertContains(response, 'Fun.java')
        self.assertContains(
            response,
            'Click here to create a downloadable zip archive for this solution.'
        )

    def test_archive_status(self):
        """Test the archive status endpoint."""
        self.assertTrue(self.client.login(username='bob', password='secret'))
        response = self.client.get(reverse('solutions:archive_status', kwargs={
            'solution_id': self.solution.id
        }))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'unavailable')

        create_archive(self.solution)

        response = self.client.get(reverse('solutions:archive_status', kwargs={
            'solution_id': self.solution.id
        }))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'available')

    def test_archive_status_access(self):
        """Test the access privileges to the archive status endpoint."""
        for user, expected_status_code in [
            (self.bob, 200),
            (self.arnold, 200),
            (self.alice, 404),
        ]:
            self.client.force_login(user)
            response = self.client.get(reverse('solutions:archive_status', kwargs={
                'solution_id': self.solution.id
            }))
            self.assertEqual(response.status_code, expected_status_code)

    def test_new_archive_access(self):
        """Test the access privileges to the archive creation."""
        create_archive(self.solution)
        for user, expected_status_code in [
            (self.bob, 200),
            (self.arnold, 200),
            (self.alice, 404),
        ]:
            self.client.force_login(user)
            response = self.client.get(reverse('solutions:archive_new', kwargs={
                'solution_id': self.solution.id
            }))
            self.assertEqual(response.status_code, expected_status_code)

    def test_archive_download(self):
        """Test archive download in solution detail view."""
        create_archive(self.solution)

        response = self.client.get(reverse('solutions:archive_download', kwargs={
            'solution_id': self.solution.id
        }), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_archive_download_access(self):
        """Test the access privileges to the archive download."""
        create_archive(self.solution)
        for user, expected_status_code in [
            (self.bob, 200),
            (self.arnold, 200),
            (self.alice, 404),
        ]:
            self.client.force_login(user)
            response = self.client.get(reverse('solutions:archive_download', kwargs={
                'solution_id': self.solution.id
            }))
            self.assertEqual(response.status_code, expected_status_code)

    def test_console_output(self):
        """Test console output tab in solution detail view."""
        self.assertTrue(self.client.login(username='bob', password='secret'))
        response = self.get_view()
        self.assertContains(response, 'STDERR Output')
        self.assertContains(response, 'STDOUT Output')

    def test_unit_tests(self):
        """test unit tests tab in solution detail view."""
        self.assertTrue(self.client.login(username='bob', password='secret'))
        response = self.get_view()
        self.assertContains(response, 'Nothing to show here.')

    def tearDown(self):
        # Remove solution and associated objects
        # to ensure clean environment for each test
        self.solution.delete()
        super().tearDown()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_MEDIA_ROOT)
        super().tearDownClass()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class SolutionFileViewTest(AccountsData, TaskData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.solution = Solution.objects.create(author=cls.alice, task=cls.published_task1)
        cls.solution_file = SolutionFile.objects.create(
            solution=cls.solution,
            file=SimpleUploadedFile('example.py', b'print("Hello World")')
        )

    def test_author_can_access_solution(self):
        self.assertTrue(self.client.login(username='alice', password='secret'))
        response = self.client.get(reverse('solutions:showfile', kwargs={
            'pk': self.solution_file.pk
        }))
        self.assertContains(response, 'example.py')
        self.assertContains(response, 'print(&quot;Hello World&quot;)')

    def test_staff_can_access_solution(self):
        self.assertTrue(self.client.login(username='arnold', password='secret'))
        response = self.client.get(reverse('solutions:showfile', kwargs={
            'pk': self.solution_file.pk
        }))
        self.assertContains(response, 'viewing a file authored by')
        self.assertContains(response, '<a href="mailto:alice@example.org">alice</a>')
        self.assertContains(response, 'example.py')
        self.assertContains(response, 'print(&quot;Hello World&quot;)')

    def test_others_cant_access_solution(self):
        self.assertTrue(self.client.login(username='bob', password='secret'))
        response = self.client.get(reverse('solutions:showfile', kwargs={
            'pk': self.solution_file.pk
        }))
        self.assertEqual(response.status_code, 404)

    def test_anonymous_cant_access_solution(self):
        response = self.client.get(reverse('solutions:showfile', kwargs={
            'pk': self.solution_file.pk
        }))
        self.assertEqual(response.status_code, 302)


class GetCheckpointTests(AccountsData, TaskData, TestCase):
    urlname = 'solutions:get-last-checkpoint'

    def setUp(self):
        self.assertTrue(self.client.login(username='alice', password='secret'))

    def test_returns_dont_cache_headers(self):
        response = self.client.get(reverse(self.urlname, kwargs={
            'slug': self.published_task1.slug,
        }))
        self.assertIn('Cache-Control', response)
        self.assertIn('no-cache', response['Cache-Control'])
        self.assertIn('max-age=0', response['Cache-Control'])

    def test_returns_empty_filelist(self):
        response = self.client.get(reverse(self.urlname, kwargs={
            'slug': self.published_task1.slug,
        }))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'success': True,
            'files': [],
        })

    def test_returns_saved_files(self):
        # also create a template to ensure it is ignored
        FileTemplate.objects.create(task=self.published_task1, name='Foo.java', contents='Foo')
        checkpoint = Checkpoint.objects.create(author=self.alice, task=self.published_task1)
        # create files in reverse alphabetical order
        # to test ordering by id instead of name
        CheckpointFile.objects.create(checkpoint=checkpoint, name='B.java', contents='B')
        CheckpointFile.objects.create(checkpoint=checkpoint, name='A.java', contents='A')
        response = self.client.get(reverse(self.urlname, kwargs={
            'slug': self.published_task1.slug,
        }))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'success': True,
            'files': [
                {'name': 'B.java', 'contents': 'B'},
                {'name': 'A.java', 'contents': 'A'},
            ],
        })

    def test_returns_file_templates(self):
        FileTemplate.objects.create(task=self.published_task1, name='Foo.java', contents='Foo')
        FileTemplate.objects.create(task=self.published_task1, name='Bar.java', contents='Bar')
        response = self.client.get(reverse(self.urlname, kwargs={
            'slug': self.published_task1.slug,
        }))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'success': True,
            'files': [
                {'name': 'Foo.java', 'contents': 'Foo'},
                {'name': 'Bar.java', 'contents': 'Bar'},
            ],
        })
