from unittest import expectedFailure

from django.test import TestCase
from django.urls import reverse

from tests.unit.accounts.mixins import SimpleAccountsData
from tests.unit.tasks.mixins import TaskData


class IndexViewTest(SimpleAccountsData, TaskData, TestCase):
    @expectedFailure
    def test_task_visibility(self):
        url = reverse("tasks:category", kwargs={"slug": self.category1.slug})
        self.client.login(username="bob", password="secret")
        response = self.client.get(url, follow=True)
        self.assertContains(response, self.published_task1.title)
        self.assertNotContains(response, self.unpublished_task1.title)
