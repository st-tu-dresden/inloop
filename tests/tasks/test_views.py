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
