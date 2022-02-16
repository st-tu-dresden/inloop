from unittest.mock import patch

from django.contrib.auth.models import Group
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

from inloop.tasks.models import Category

from tests.accounts.mixins import SimpleAccountsData
from tests.tasks.mixins import TaskData


class CategoryViewTest(SimpleAccountsData, TaskData, TestCase):
    def setUp(self):
        self.assertTrue(self.client.login(username="bob", password="secret"))

    def get_url(self, slug):
        return reverse("tasks:category", kwargs={"slug": slug})

    def test_view_empty_category(self):
        category = Category.objects.create(name="Empty category")
        response = self.client.get(self.get_url(category.slug))
        self.assertContains(response, "Nothing to do here")

    def test_view_all_unpublished_category(self):
        category = Category.objects.create(name="Unpublished tasks")
        self.unpublished_task1.category = category
        self.unpublished_task1.save()
        response = self.client.get(self.get_url(category.slug))
        self.assertContains(response, self.unpublished_task1.title)
        self.assertContains(response, '<tr id="task-row-1" class="tasks-unpublished">')
        self.assertNotContains(response, "Nothing to do here")

    def test_view_all_published_category(self):
        category = Category.objects.create(name="Published tasks")
        self.published_task1.category = category
        self.published_task1.save()
        response = self.client.get(self.get_url(category.slug))
        self.assertContains(response, self.published_task1.title)
        self.assertNotContains(response, "Nothing to do here")
        self.assertNotContains(response, '<tr id="task-row-1" class="tasks-unpublished">')

    def test_view_category(self):
        response = self.client.get(self.get_url(self.category1.slug))
        self.assertContains(response, self.published_task1.title)
        self.assertContains(response, self.published_task2.title)
        self.assertContains(response, self.unpublished_task1.title)
        self.assertContains(response, self.unpublished_task2.title)
        self.assertNotContains(response, "Nothing to do here")


@patch("inloop.tasks.views.sendfile")
class AttachmentViewTest(SimpleAccountsData, TaskData, TestCase):
    def setUp(self):
        self.assertTrue(self.client.login(username="bob", password="secret"))

    def get_url(self, slug, path):
        # for some ugly reason this is mounted in the solutions namespace :(
        return reverse("solutions:serve_attachment", kwargs={"slug": slug, "path": path})

    def test_view_published_attachment_without_group(self, mocked_sendfile):
        mocked_sendfile.return_value = HttpResponse("this would be image data")
        response = self.client.get(self.get_url(self.published_task1.slug, "images/foo.png"))
        mocked_sendfile.assert_called_once()
        self.assertContains(response, "this would be image data")

    def test_view_published_attachment_with_group(self, mocked_sendfile):
        # given a task that can only be seen by the group that alice is in ...
        group_with_alice = Group.objects.create(name="Group with alice")
        self.alice.groups.add(group_with_alice)
        self.published_task1.group = group_with_alice
        self.published_task1.save()
        mocked_sendfile.return_value = HttpResponse("alice should see this")

        # ... bob should get a 404
        response = self.client.get(self.get_url(self.published_task1.slug, "images/foo.png"))
        self.assertEqual(response.status_code, 404)
        mocked_sendfile.assert_not_called()

        # ... alice should be able to see the attachment
        self.assertTrue(self.client.login(username="alice", password="secret"))
        response = self.client.get(self.get_url(self.published_task1.slug, "images/foo.png"))
        mocked_sendfile.assert_called_once()
        self.assertContains(response, "alice should see this")

    def test_view_unpublished_attachment(self, mocked_sendfile):
        response = self.client.get(self.get_url(self.unpublished_task1.slug, "images/foo.png"))
        self.assertEqual(response.status_code, 404)
        mocked_sendfile.assert_not_called()

    def test_unallowed_subdirectory(self, mocked_sendfile):
        response = self.client.get(self.get_url(self.published_task1.slug, "not-allowed/foo.png"))
        self.assertEqual(response.status_code, 404)
        mocked_sendfile.assert_not_called()

    def test_reject_path_traversal(self, mocked_sendfile):
        response = self.client.get(self.get_url(self.published_task1.slug, "images/../foo.png"))
        self.assertEqual(response.status_code, 404)
        mocked_sendfile.assert_not_called()
