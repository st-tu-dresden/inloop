import os
import shutil
from datetime import timedelta
from json import JSONDecodeError
from tempfile import mkdtemp
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings, tag
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_str

from constance.test import override_config

from inloop.solutions.models import (
    Checkpoint,
    CheckpointFile,
    Solution,
    SolutionFile,
    create_archive,
)
from inloop.solutions.views import parse_json_payload
from inloop.tasks.models import FileTemplate
from inloop.testrunner.models import TestResult

from tests.accounts.mixins import AccountsData, SimpleAccountsData
from tests.tasks.mixins import TaskData


class SolutionStatusViewTest(TaskData, SimpleAccountsData, TestCase):
    def setUp(self):
        super().setUp()
        self.solution = Solution.objects.create(author=self.bob, task=self.published_task1)

    def test_pending_state(self):
        self.assertTrue(self.client.login(username="bob", password="secret"))
        response = self.client.get(reverse("solutions:status", kwargs={"id": self.solution.id}))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"status": "pending", "solution_id": self.solution.id},
        )

    def test_only_owner_can_access(self):
        self.assertTrue(self.client.login(username="alice", password="secret"))
        response = self.client.get(reverse("solutions:status", kwargs={"id": self.solution.id}))
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
        response = self.client.get(
            reverse(
                "solutions:detail",
                kwargs={"slug": self.solution.task.slug, "scoped_id": self.solution.scoped_id},
            ),
            follow=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("solutions:list", kwargs={"slug": self.solution.task.slug})
        )


TEST_MEDIA_ROOT = mkdtemp()


@tag("slow")
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
            author=self.bob, task=self.published_task1, passed=False
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
            file=SimpleUploadedFile("Fun.java", "public class Fun {}".encode()),
        )
        self.solution.passed = self.test_result.is_success()
        self.solution.save()

    def get_view(self):
        response = self.client.get(
            reverse(
                "solutions:detail",
                kwargs={"slug": self.solution.task.slug, "scoped_id": self.solution.scoped_id},
            ),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        return response

    def test_overview(self):
        """Test overview tab in solution detail view."""
        self.assertTrue(self.client.login(username="bob", password="secret"))
        response = self.get_view()
        self.assertContains(response, "Congratulations, your solution passed all tests.")
        self.assertContains(response, "Fun.java")
        self.assertContains(
            response, "Click here to create a downloadable zip archive for this solution."
        )

    def test_archive_status(self):
        """Test the archive status endpoint."""
        self.assertTrue(self.client.login(username="bob", password="secret"))
        response = self.client.get(
            reverse("solutions:archive_status", kwargs={"solution_id": self.solution.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "unavailable")

        create_archive(self.solution)

        response = self.client.get(
            reverse("solutions:archive_status", kwargs={"solution_id": self.solution.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "available")

    def test_archive_status_access(self):
        """Test the access privileges to the archive status endpoint."""
        for user, expected_status_code in [
            (self.bob, 200),
            (self.arnold, 200),
            (self.alice, 404),
        ]:
            self.client.force_login(user)
            response = self.client.get(
                reverse("solutions:archive_status", kwargs={"solution_id": self.solution.id})
            )
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
            response = self.client.get(
                reverse("solutions:archive_new", kwargs={"solution_id": self.solution.id})
            )
            self.assertEqual(response.status_code, expected_status_code)

    def test_archive_download(self):
        """Test archive download in solution detail view."""
        create_archive(self.solution)

        response = self.client.get(
            reverse("solutions:archive_download", kwargs={"solution_id": self.solution.id}),
            follow=True,
        )
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
            response = self.client.get(
                reverse("solutions:archive_download", kwargs={"solution_id": self.solution.id})
            )
            self.assertEqual(response.status_code, expected_status_code)

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


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class SolutionFileViewTest(AccountsData, TaskData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.solution = Solution.objects.create(author=cls.alice, task=cls.published_task1)
        cls.solution_file = SolutionFile.objects.create(
            solution=cls.solution, file=SimpleUploadedFile("example.py", b'print("Hello World")')
        )

    def test_author_can_access_solution(self):
        self.assertTrue(self.client.login(username="alice", password="secret"))
        response = self.client.get(
            reverse("solutions:showfile", kwargs={"pk": self.solution_file.pk})
        )
        self.assertContains(response, "example.py")
        self.assertContains(response, "print(&quot;Hello World&quot;)")

    def test_staff_can_access_solution(self):
        self.assertTrue(self.client.login(username="arnold", password="secret"))
        response = self.client.get(
            reverse("solutions:showfile", kwargs={"pk": self.solution_file.pk})
        )
        self.assertContains(response, "viewing a file authored by")
        self.assertContains(response, '<a href="mailto:alice@example.org">alice</a>')
        self.assertContains(response, "example.py")
        self.assertContains(response, "print(&quot;Hello World&quot;)")

    def test_others_cant_access_solution(self):
        self.assertTrue(self.client.login(username="bob", password="secret"))
        response = self.client.get(
            reverse("solutions:showfile", kwargs={"pk": self.solution_file.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_anonymous_cant_access_solution(self):
        response = self.client.get(
            reverse("solutions:showfile", kwargs={"pk": self.solution_file.pk})
        )
        self.assertEqual(response.status_code, 302)


class GetCheckpointTests(AccountsData, TaskData, TestCase):
    urlname = "solutions:get-last-checkpoint"

    def setUp(self):
        self.assertTrue(self.client.login(username="alice", password="secret"))

    def test_returns_dont_cache_headers(self):
        response = self.client.get(
            reverse(
                self.urlname,
                kwargs={
                    "slug": self.published_task1.slug,
                },
            )
        )
        self.assertIn("Cache-Control", response)
        self.assertIn("no-cache", response["Cache-Control"])
        self.assertIn("max-age=0", response["Cache-Control"])

    def test_returns_empty_filelist(self):
        response = self.client.get(
            reverse(
                self.urlname,
                kwargs={
                    "slug": self.published_task1.slug,
                },
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                "success": True,
                "files": [],
            },
        )

    def test_returns_saved_files(self):
        # also create a template to ensure it is ignored
        FileTemplate.objects.create(task=self.published_task1, name="Foo.java", contents="Foo")
        checkpoint = Checkpoint.objects.create(author=self.alice, task=self.published_task1)
        # create files in reverse alphabetical order
        # to test ordering by id instead of name
        CheckpointFile.objects.create(checkpoint=checkpoint, name="B.java", contents="B")
        CheckpointFile.objects.create(checkpoint=checkpoint, name="A.java", contents="A")
        response = self.client.get(
            reverse(
                self.urlname,
                kwargs={
                    "slug": self.published_task1.slug,
                },
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                "success": True,
                "files": [
                    {"name": "B.java", "contents": "B"},
                    {"name": "A.java", "contents": "A"},
                ],
            },
        )

    def test_returns_file_templates(self):
        FileTemplate.objects.create(task=self.published_task1, name="Foo.java", contents="Foo")
        FileTemplate.objects.create(task=self.published_task1, name="Bar.java", contents="Bar")
        response = self.client.get(
            reverse(
                self.urlname,
                kwargs={
                    "slug": self.published_task1.slug,
                },
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                "success": True,
                "files": [
                    {"name": "Foo.java", "contents": "Foo"},
                    {"name": "Bar.java", "contents": "Bar"},
                ],
            },
        )


class EditorVisibilityTest(SimpleAccountsData, TaskData, TestCase):
    def test_group_access(self):
        group = Group.objects.create(name="Group1")
        self.published_task1.group = group
        self.published_task1.save()
        self.alice.groups.add(group)
        self.assertTrue(self.client.login(username="alice", password="secret"))
        response = self.client.get(reverse("solutions:editor", args=["task-1"]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.client.login(username="bob", password="secret"))
        response = self.client.get(reverse("solutions:editor", args=["task-1"]))
        self.assertEqual(response.status_code, 404)

    def test_redirect_to_slug(self):
        self.assertTrue(self.client.login(username="alice", password="secret"))
        response = self.client.get(reverse("solutions:editor", args=["Task1"]))
        self.assertRedirects(response, reverse("solutions:editor", args=["task-1"]))


class JsonValidationTest(TestCase):
    def test_invalid_json(self):
        with self.assertRaises(JSONDecodeError):
            parse_json_payload(b"{ not json }")

    def test_wrong_type1(self):
        with self.assertRaises(ValidationError):
            parse_json_payload(b"[]")

    def test_wrong_type2(self):
        with self.assertRaises(ValidationError):
            parse_json_payload(b'{"files": {}}')

    def test_wrong_type3(self):
        with self.assertRaises(ValidationError):
            parse_json_payload(b'{"files": {"name": "", "contents": false}}')

    def test_missing_key1(self):
        with self.assertRaises(ValidationError):
            parse_json_payload(b"{}")

    def test_missing_key2(self):
        with self.assertRaises(ValidationError):
            parse_json_payload(b'{"files": {"name": "", "wrong_key": ""}}')


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class EditorSubmitTest(SimpleAccountsData, TaskData, TestCase):
    urlname = "solutions:editor"

    def setUp(self):
        # sync in-memory model state after transaction rollbacks
        self.published_task1.refresh_from_db()
        self.assertTrue(self.client.login(username="alice", password="secret"))

    def assertJsonResponse(self, response, expected, *, status_code=200):
        self.assertEqual(response.status_code, status_code)
        self.assertJSONEqual(force_str(response.content), expected)

    def test_lgin_required(self):
        self.client.logout()
        url = reverse(self.urlname, args=["task-1"])
        self.assertRedirects(self.client.post(url), f"{settings.LOGIN_URL}?next={url}")

    def test_invalid_json(self):
        response = self.client.post(
            reverse(self.urlname, args=["task-1"]),
            content_type="application/json",
            data="{ not json }",
        )
        self.assertJsonResponse(response, {"error": "invalid json"}, status_code=400)

    def test_invalid_data(self):
        response = self.client.post(
            reverse(self.urlname, args=["task-1"]),
            content_type="application/json",
            data={"files": "foo"},
        )
        self.assertJsonResponse(response, {"success": False, "reason": "invalid data"})

    @override_config(ALLOWED_FILENAME_EXTENSIONS=".py")
    def test_wrong_file_extension(self):
        response = self.client.post(
            reverse(self.urlname, args=["task-1"]),
            content_type="application/json",
            data={"files": [{"name": "Example.java", "contents": ""}]},
        )
        self.assertContains(response, "files contain disallowed filename extensions")

    def test_deadline_expired(self):
        self.published_task1.deadline = timezone.now() - timedelta(seconds=1)
        self.published_task1.save()
        response = self.client.post(
            reverse(self.urlname, args=["task-1"]),
            content_type="application/json",
            data={"files": []},
        )
        self.assertJsonResponse(
            response, {"success": False, "reason": "The deadline for this task has passed."}
        )

    def test_submission_limit_exceeded(self):
        self.published_task1.max_submissions = 0
        self.published_task1.save()
        response = self.client.post(
            reverse(self.urlname, args=["task-1"]),
            content_type="application/json",
            data={"files": [{"name": "Example.java", "contents": ""}]},
        )
        self.assertJsonResponse(
            response, {"success": False, "reason": "You cannot submit more than 0 solutions."}
        )

    def test_successful_submit_with_limit(self):
        self.published_task1.max_submissions = 2
        self.published_task1.save()
        with patch("inloop.solutions.models.solution_submitted") as signal_mock:
            response = self.client.post(
                reverse(self.urlname, args=["task-1"]),
                content_type="application/json",
                data={"files": [{"name": "Example.java", "contents": ""}]},
            )
            signal_mock.send.assert_called_once()
        self.assertJsonResponse(
            response, {"success": True, "submission_limit": 2, "num_submissions": 1}
        )

    def test_successful_submit_without_limit(self):
        with patch("inloop.solutions.models.solution_submitted") as signal_mock:
            response = self.client.post(
                reverse(self.urlname, args=["task-1"]),
                content_type="application/json",
                data={"files": [{"name": "Example.java", "contents": ""}]},
            )
            signal_mock.send.assert_called_once()
        self.assertJsonResponse(response, {"success": True})

    @override_config(IMMEDIATE_FEEDBACK=False)
    def test_feedback_disabled(self):
        with patch("inloop.solutions.models.solution_submitted") as signal_mock:
            response = self.client.post(
                reverse(self.urlname, args=["task-1"]),
                content_type="application/json",
                data={"files": [{"name": "Example.java", "contents": ""}]},
            )
            signal_mock.send.assert_not_called()
        self.assertJsonResponse(response, {"success": True})


class EditorSaveTest(SimpleAccountsData, TaskData, TestCase):
    urlname = "solutions:save-checkpoint"

    def setUp(self):
        self.assertTrue(self.client.login(username="alice", password="secret"))

    def test_login_required(self):
        self.client.logout()
        url = reverse(self.urlname, args=["task-1"])
        self.assertRedirects(self.client.post(url), f"{settings.LOGIN_URL}?next={url}")

    def test_post_required(self):
        response = self.client.get(reverse(self.urlname, args=["task-1"]))
        self.assertEqual(response.status_code, 405)

    def test_invalid_json(self):
        response = self.client.post(
            reverse(self.urlname, args=["task-1"]),
            content_type="application/json",
            data="{ not json }",
        )
        self.assertContains(response, "invalid json", status_code=400)

    def test_files_are_saved(self):
        response = self.client.post(
            reverse(self.urlname, args=["task-1"]),
            content_type="application/json",
            data={"files": [{"name": "foo.txt", "contents": "bar"}]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        checkpoint = Checkpoint.objects.get(task=self.published_task1, author=self.alice)
        files = list(checkpoint.checkpointfile_set.all())
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, "foo.txt")
        self.assertEqual(files[0].contents, "bar")

    def test_save_empty_fileset(self):
        response = self.client.post(
            reverse(self.urlname, args=["task-1"]),
            content_type="application/json",
            data={"files": []},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        checkpoint = Checkpoint.objects.get(task=self.published_task1, author=self.alice)
        self.assertEqual(list(checkpoint.checkpointfile_set.all()), [])

    def test_incomplete_json(self):
        response = self.client.post(
            reverse(self.urlname, args=["task-1"]),
            content_type="application/json",
            data={"wrong_key": []},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["success"])
