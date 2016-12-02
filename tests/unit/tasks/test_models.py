from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from inloop.solutions.models import Solution
from inloop.tasks.models import Category, Task

from tests.unit.accounts.mixins import SimpleAccountsData
from tests.unit.tasks.mixins import TaskData


class TaskTests(SimpleAccountsData, TaskData, TestCase):
    def test_slugify_on_save(self):
        task = Task.objects.create(
            title="Some Task III (winter term 2010/2011)",
            category=self.category1,
            pubdate=timezone.now()
        )
        self.assertEqual(task.slug, "some-task-iii")

    def test_is_published(self):
        self.assertTrue(self.published_task1.is_published)
        self.assertFalse(self.unpublished_task1.is_published)

    def test_is_expired(self):
        self.assertFalse(self.published_task1.is_expired)
        self.assertFalse(self.unpublished_task1.is_expired)

    def test_is_completed_by(self):
        Solution.objects.create(author=self.bob, task=self.published_task1)
        self.assertFalse(self.published_task1.is_completed_by(self.bob))
        Solution.objects.create(author=self.bob, task=self.published_task1, passed=True)
        self.assertTrue(self.published_task1.is_completed_by(self.bob))
        self.assertFalse(self.published_task2.is_completed_by(self.bob))

    def test_required_fields(self):
        self.assertSetEqual(Task.objects.required_fields, {
            "title", "description", "category", "pubdate", "system_name"
        })


class TaskCategoryTests(SimpleAccountsData, TaskData, TestCase):
    def test_slugify_on_save(self):
        category = Category.objects.create(name="Test category")
        self.assertEqual(category.slug, "test-category")

    def test_completion_info_initial(self):
        for user in [self.bob, self.alice]:
            self.assertDictEqual(self.category1.completion_info(user), {
                "num_completed": 0,
                "num_published": 2,
                "progress": 0
            })
        for user in [self.bob, self.alice]:
            self.assertDictEqual(self.category2.completion_info(user), {
                "num_completed": 0,
                "num_published": 0,
                "progress": 0
            })

    def test_completion_info(self):
        for i in range(2):
            Solution.objects.create(author=self.bob, task=self.published_task1, passed=True)
            Solution.objects.create(author=self.alice, task=self.published_task1, passed=True)

        for user in [self.bob, self.alice]:
            self.assertDictEqual(self.category1.completion_info(user), {
                "num_completed": 1,
                "num_published": 2,
                "progress": 50
            })

        for i in range(2):
            Solution.objects.create(author=self.bob, task=self.published_task2, passed=True)
            Solution.objects.create(author=self.alice, task=self.published_task2, passed=True)

        for user in [self.bob, self.alice]:
            self.assertDictEqual(self.category1.completion_info(user), {
                "num_completed": 2,
                "num_published": 2,
                "progress": 100
            })


class CompletedByTests(SimpleAccountsData, TaskData, TestCase):
    def test_no_solutions(self):
        for user in [self.bob, self.alice]:
            self.assertFalse(Task.objects.completed_by(user))
            self.assertFalse(self.category1.task_set.completed_by(user))
            self.assertFalse(self.category2.task_set.completed_by(user))

    def test_only_failed_solutions(self):
        Solution.objects.create(author=self.bob, task=self.published_task1)
        Solution.objects.create(author=self.alice, task=self.published_task2)
        for user in [self.bob, self.alice]:
            self.assertFalse(Task.objects.completed_by(user))
            self.assertFalse(self.category1.task_set.completed_by(user))
            self.assertFalse(self.category2.task_set.completed_by(user))

    def test_with_bobs_passed_solution(self):
        Solution.objects.create(author=self.bob, task=self.published_task1)
        Solution.objects.create(author=self.bob, task=self.published_task2)
        Solution.objects.create(author=self.bob, task=self.published_task1, passed=True)

        self.assertEqual(len(Task.objects.completed_by(self.bob)), 1)
        self.assertEqual(len(Task.objects.completed_by(self.alice)), 0)

        self.assertEqual(len(self.category1.task_set.completed_by(self.bob)), 1)
        self.assertEqual(len(self.category2.task_set.completed_by(self.bob)), 0)
        self.assertEqual(len(self.category1.task_set.completed_by(self.alice)), 0)

    def test_completed_same_task(self):
        for i in range(3):
            Solution.objects.create(author=self.bob, task=self.published_task1, passed=True)
        completed = Task.objects.completed_by(self.bob)
        self.assertSequenceEqual(completed, [self.published_task1])

    def test_completed_different_tasks(self):
        for i in range(3):
            Solution.objects.create(author=self.bob, task=self.published_task1, passed=True)
            Solution.objects.create(author=self.bob, task=self.published_task2, passed=True)
        completed = self.category1.task_set.completed_by(self.bob)
        self.assertSequenceEqual(completed, [self.published_task1, self.published_task2])

    def test_inverse_op(self):
        Solution.objects.create(author=self.bob, task=self.published_task1, passed=True)
        self.assertSequenceEqual(Task.objects.not_completed_by(self.bob), [
            self.published_task2, self.unpublished_task1, self.unpublished_task2
        ])
        self.assertSequenceEqual(self.category1.task_set.not_completed_by(self.bob), [
            self.published_task2, self.unpublished_task1, self.unpublished_task2
        ])
        self.assertFalse(self.category2.task_set.not_completed_by(self.bob))


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
