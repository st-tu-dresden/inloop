from django.test import TestCase
from django.urls import reverse

from tests.unit.accounts.mixins import SimpleAccountsData
from tests.unit.tasks.mixins import TaskData


class IndexViewTest(SimpleAccountsData, TaskData, TestCase):
    def test_task_visibility(self):
        url = reverse("tasks:category", kwargs={"slug": self.category1.slug})
        self.assertTrue(self.client.login(username="bob", password="secret"))
        response = self.client.get(url, follow=True)
        self.assertContains(response, self.published_task1.title)


class TaskDetailViewTest(SimpleAccountsData, TaskData, TestCase):
    def test_redirect_to_slug(self):
        name_url = reverse("tasks:detail", args=["Task1"])
        slug_url = reverse("tasks:detail", args=["task-1"])
        self.assertTrue(self.client.login(username="bob", password="secret"))
        self.assertRedirects(self.client.get(name_url), slug_url)
