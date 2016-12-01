from doctest import DocTestSuite

from django.core.exceptions import ValidationError
from django.test import TestCase

from inloop.solutions.models import Solution
from inloop.tasks import models
from inloop.tasks.models import Category, Task

from tests.unit.accounts.mixins import SimpleAccountsData
from tests.unit.tasks.mixins import TaskData


def load_tests(loader, tests, ignore):
    """Initialize doctests for this module."""
    tests.addTests(DocTestSuite(models))
    return tests


class TaskTests(TaskData, TestCase):
    def test_task_is_published(self):
        self.assertTrue(self.published_task1.is_published())
        self.assertFalse(self.unpublished_task1.is_published())

    def test_invalid_inputs(self):
        with self.assertRaises(ValidationError):
            Task.objects.create(pubdate="abc")

        with self.assertRaises(ValidationError):
            Task.objects.create(deadline="abc")


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


class GetOrCreateTests(TestCase):
    def setUp(self):
        Category.objects.create(name="Test category")

    def test_returns_existing_category(self):
        before = Category.objects.count()
        category = Category.objects.get_or_create("Test category")
        after = Category.objects.count()
        self.assertEqual(category.name, "Test category")
        self.assertEqual(before, after)

    def test_returns_new_category(self):
        before = Category.objects.count()
        category = Category.objects.get_or_create("Another category")
        after = Category.objects.count()
        self.assertEqual(category.name, "Another category")
        self.assertEqual(before, after - 1)


class TaskManagerTests(TestCase):
    def setUp(self):
        self.manager = Task.objects
        self.valid_json = {"title": "Test title", "category": "Lesson",
                           "pubdate": "2015-05-01 13:37:00"}

    def test_validate_empty(self):
        with self.assertRaises(ValueError):
            self.manager._validate(dict())

    def test_validate_valid(self):
        self.manager._validate(self.valid_json)

    def test_update(self):
        input = Task()
        task = self.manager._update_task(input, self.valid_json)

        self.assertIs(task, input)
        self.assertEqual(task.title, "Test title")
        self.assertEqual(task.slug, "test-title")
        self.assertEqual(task.category.name, "Lesson")

        pubdate = task.pubdate.strftime("%Y-%m-%d %H:%M:%S")
        self.assertEqual(pubdate, self.valid_json["pubdate"])

    def test_save_task_with_valid_json(self):
        task = Task.objects.get_or_create_json(self.valid_json, "Test title")
        task.save()
