from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from inloop.solutions.models import Solution
from inloop.tasks.models import Category, Task

from tests.unit.accounts.mixins import SimpleAccountsData
from tests.unit.tasks.mixins import TaskData


class TaskTests(TaskData, TestCase):
    def test_slugify_on_save(self):
        task = Task.objects.create(
            title="Some Task III (winter term 2010/2011)",
            category=self.category1,
            pubdate=timezone.now()
        )
        self.assertEqual(task.slug, "some-task-iii")

    def test_task_is_published(self):
        self.assertTrue(self.published_task1.is_published())
        self.assertFalse(self.unpublished_task1.is_published())

    def test_required_fields(self):
        self.assertSetEqual(Task.objects.required_fields, {
            "title", "description", "category", "pubdate", "system_name"
        })


class TaskCategoryTests(SimpleAccountsData, TaskData, TestCase):
    def test_slugify_on_save(self):
        category = Category.objects.create(name="Test category")
        self.assertEqual(category.slug, "test-category")

    def test_completed_tasks_empty_category(self):
        empty_category = Category.objects.create(name="Empty category")
        for user in [self.bob, self.alice]:
            self.assertFalse(empty_category.completed_tasks_for_user(user).exists())

    def test_tasks_uncompleted(self):
        Solution.objects.create(author=self.bob, task=self.published_task1)
        self.assertFalse(self.category1.completed_tasks_for_user(self.bob).exists())

    def test_tasks_completed(self):
        Solution.objects.create(author=self.bob, task=self.published_task1, passed=True)
        self.assertTrue(self.category1.completed_tasks_for_user(self.bob).exists())

    def test_completed_same_task(self):
        for i in range(2):
            Solution.objects.create(author=self.bob, task=self.published_task1, passed=True)
        completed = self.category1.completed_tasks_for_user(self.bob)
        self.assertSequenceEqual(completed, [self.published_task1])

    def test_completed_different_tasks(self):
        for i in range(2):
            Solution.objects.create(author=self.bob, task=self.published_task1, passed=True)
            Solution.objects.create(author=self.bob, task=self.published_task2, passed=True)
        completed = self.category1.completed_tasks_for_user(self.bob)
        self.assertSequenceEqual(completed, [self.published_task1, self.published_task2])


class UpdateOrCreateRelatedTest(TestCase):
    def setUp(self):
        self.data = {
            "title": "Test title",
            "category": "Beginner",
            "pubdate": "2016-12-01 13:37:00+0100",
            "description": "Task description"
        }

    def test_create(self):
        task = Task.objects.update_or_create_related(system_name="TestTask", data=self.data)
        self.assertEqual(task.title, "Test title")
        self.assertEqual(task.system_name, "TestTask")
        self.assertEqual(task.category.name, "Beginner")
        self.assertTrue(Category.objects.get(name="Beginner"))

    def test_update(self):
        task1 = Task.objects.update_or_create_related(system_name="TestTask", data=self.data)
        self.data["title"] = "Another title"
        self.data["category"] = "Advanced"
        task2 = Task.objects.update_or_create_related(system_name="TestTask", data=self.data)
        task1.refresh_from_db()
        self.assertEqual(task1.id, task2.id)
        self.assertEqual(task1.title, "Another title")
        self.assertEqual(task1.category.name, "Advanced")
        self.assertTrue(Category.objects.get(name="Beginner"))
        self.assertTrue(Category.objects.get(name="Advanced"))

    def test_invalid_date(self):
        self.data["pubdate"] = "invalid"
        with self.assertRaises(ValidationError):
            Task.objects.update_or_create_related(system_name="TestTask", data=self.data)

    def test_missing_data(self):
        self.data.pop("title")
        with self.assertRaises(ValidationError):
            Task.objects.update_or_create_related(system_name="TestTask", data=self.data)

    def test_invalid_key(self):
        self.data["invalid_key"] = "invalid"
        Task.objects.update_or_create_related(system_name="TestTask", data=self.data)
