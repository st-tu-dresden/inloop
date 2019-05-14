from django.test import TestCase
from django.urls import reverse

from tests.accounts.mixins import SimpleAccountsData
from tests.decorators import assert_login
from tests.tasks.mixins import TaskData


class IndexViewTest(SimpleAccountsData, TaskData, TestCase):
    @assert_login("bob", "secret")
    def setUp(self):
        url = reverse("tasks:category", kwargs={"slug": self.category1.slug})
        self.response = self.client.get(url, follow=True)

    def test_task_visibility(self):
        self.assertContains(self.response, self.published_task1.title)
        self.assertContains(self.response, self.published_task2.title)
        self.assertContains(self.response, self.unpublished_task1.title)
        self.assertContains(self.response, self.unpublished_task2.title)

    def test_task_styling(self):
        html = str(self.response.rendered_content)
        self.assertTrue("<tr style=\"color: lightgrey;\"" in html)
        self.assertTrue("<tr>" in html)


class TaskDetailViewTest(SimpleAccountsData, TaskData, TestCase):
    @assert_login("bob", "secret")
    def test_redirect_to_slug(self):
        name_url = reverse("tasks:detail", args=["Task1"])
        slug_url = reverse("tasks:detail", args=["task-1"])
        self.assertRedirects(self.client.get(name_url), slug_url)
