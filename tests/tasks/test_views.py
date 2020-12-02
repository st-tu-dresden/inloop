from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from tests.accounts.mixins import SimpleAccountsData
from tests.tasks.mixins import TaskData


class IndexViewTest(SimpleAccountsData, TaskData, TestCase):
    def setUp(self):
        url = reverse("tasks:category", kwargs={"slug": self.category1.slug})
        self.assertTrue(self.client.login(username="bob", password="secret"))
        self.response = self.client.get(url, follow=True)

    def test_task_visibility(self):
        self.assertContains(self.response, self.published_task1.title)
        self.assertContains(self.response, self.published_task2.title)
        self.assertContains(self.response, self.unpublished_task1.title)
        self.assertContains(self.response, self.unpublished_task2.title)

    def test_task_styling(self):
        html = str(self.response.rendered_content)
        self.assertTrue('<tr style="color: lightgrey;"' in html)
        self.assertTrue("<tr>" in html)


class TaskDetailViewTest(SimpleAccountsData, TaskData, TestCase):
    def test_redirect_to_slug(self):
        name_url = reverse("tasks:detail", args=["Task1"])
        slug_url = reverse("tasks:detail", args=["task-1"])
        self.assertTrue(self.client.login(username="bob", password="secret"))
        self.assertRedirects(self.client.get(name_url), slug_url)

    def test_redirect_to_editor(self):
        old_detail_url = reverse("tasks:redirect-to-editor", args=["task-1"])
        editor_url = reverse("solutions:editor", args=["task-1"])
        self.assertTrue(self.client.login(username="bob", password="secret"))
        self.assertRedirects(self.client.get(old_detail_url), editor_url)


class TaskVisibilityTest(SimpleAccountsData, TaskData, TestCase):
    def test_group_access(self):
        group = Group.objects.create(name="Group1")
        self.published_task1.group = group
        self.published_task1.save()
        self.alice.groups.add(group)
        self.assertTrue(self.client.login(username="alice", password="secret"))
        response = self.client.get(reverse("tasks:detail", args=["task-1"]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.client.login(username="bob", password="secret"))
        response = self.client.get(reverse("tasks:detail", args=["task-1"]))
        self.assertEqual(response.status_code, 404)
