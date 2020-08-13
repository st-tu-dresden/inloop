from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from constance.test import override_config

from inloop.solutions.models import Solution
from inloop.tasks.models import Category, Task

from tests.accounts.mixins import SimpleAccountsData
from tests.tasks.mixins import TaskData


class TaskTests(SimpleAccountsData, TaskData, TestCase):
    def test_slugify_on_save(self):
        task = Task.objects.create(
            title='Some Task III (winter term 2010/2011)',
            category=self.category1,
            pubdate=timezone.now()
        )
        self.assertEqual(task.slug, 'some-task-iii')

    def test_is_published(self):
        self.assertTrue(self.published_task1.is_published)
        self.assertFalse(self.unpublished_task1.is_published)

    def test_is_not_expired_when_no_deadline(self):
        self.assertFalse(self.published_task1.is_expired)
        self.assertFalse(self.unpublished_task1.is_expired)

    def test_is_expired_with_no_tolerance(self):
        now = timezone.now()
        task = Task.objects.create(
            title='Test Task',
            category=self.category1,
            pubdate=now,
            deadline=(now - timedelta(seconds=1))
        )
        self.assertTrue(task.is_expired)

    @override_config(DEADLINE_TOLERANCE=30)
    def test_is_expired_with_tolerance(self):
        now = timezone.now()
        task = Task.objects.create(
            title='Test Task',
            category=self.category1,
            pubdate=now,
            deadline=(now - timedelta(seconds=31))
        )
        self.assertTrue(task.is_expired)

    @override_config(DEADLINE_TOLERANCE=30)
    def test_is_not_expired_with_tolerance(self):
        now = timezone.now()
        task = Task.objects.create(
            title='Test Task',
            category=self.category1,
            pubdate=now,
            deadline=(now - timedelta(seconds=29))
        )
        self.assertFalse(task.is_expired)

    def test_is_completed_by(self):
        Solution.objects.create(author=self.bob, task=self.published_task1)
        self.assertFalse(self.published_task1.is_completed_by(self.bob))
        Solution.objects.create(author=self.bob, task=self.published_task1, passed=True)
        self.assertTrue(self.published_task1.is_completed_by(self.bob))
        self.assertFalse(self.published_task2.is_completed_by(self.bob))

    def test_default_submission_limit(self):
        self.assertIsNone(self.published_task1.max_submissions)
        self.assertEqual(self.published_task1.submission_limit, -1)
        self.assertFalse(self.published_task1.has_submission_limit)

    @override_config(MAX_SUBMISSIONS=10)
    def test_custom_submission_limit(self):
        self.assertIsNone(self.published_task1.max_submissions)
        self.assertEqual(self.published_task1.submission_limit, 10)
        self.assertTrue(self.published_task1.has_submission_limit)

    @override_config(MAX_SUBMISSIONS=0)
    def test_custom_submission_limit_when_zero(self):
        self.assertIsNone(self.published_task1.max_submissions)
        self.assertEqual(self.published_task1.submission_limit, 0)
        self.assertTrue(self.published_task1.has_submission_limit)

    def test_submission_limit_local_override(self):
        task1 = Task.objects.create(
            title='Test Task 1',
            system_name='TestTask1',
            category=self.category1,
            pubdate=timezone.now(),
            max_submissions=0
        )
        task2 = Task.objects.create(
            title='Test Task 2',
            system_name='TestTask2',
            category=self.category1,
            pubdate=timezone.now(),
            max_submissions=10
        )
        self.assertEqual(task1.submission_limit, 0)
        self.assertTrue(task1.has_submission_limit)
        self.assertEqual(task2.submission_limit, 10)
        self.assertTrue(task2.has_submission_limit)

    @override_config(MAX_SUBMISSIONS=10)
    def test_custom_submission_limit_local_override(self):
        task = Task.objects.create(
            title='Test Task',
            system_name='TestTask',
            category=self.category1,
            pubdate=timezone.now(),
            max_submissions=15
        )
        self.assertEqual(task.submission_limit, 15)
        self.assertTrue(task.has_submission_limit)


class TaskCategoryTests(SimpleAccountsData, TaskData, TestCase):
    def test_slugify_on_save(self):
        category = Category.objects.create(name='Test category')
        self.assertEqual(category.slug, 'test-category')

    def test_completion_info_initial(self):
        for user in [self.bob, self.alice]:
            self.assertDictEqual(self.category1.completion_info(user), {
                'num_completed': 0,
                'num_published': 2,
                'is_completed': False,
                'progress': 0
            })
        for user in [self.bob, self.alice]:
            self.assertDictEqual(self.category2.completion_info(user), {
                'num_completed': 0,
                'num_published': 0,
                'is_completed': True,
                'progress': 0
            })

    def test_completion_info(self):
        for _ in range(2):
            Solution.objects.create(author=self.bob, task=self.published_task1, passed=True)
            Solution.objects.create(author=self.alice, task=self.published_task1, passed=True)

        for user in [self.bob, self.alice]:
            self.assertDictEqual(self.category1.completion_info(user), {
                'num_completed': 1,
                'num_published': 2,
                'is_completed': False,
                'progress': 50
            })

        for _ in range(2):
            Solution.objects.create(author=self.bob, task=self.published_task2, passed=True)
            Solution.objects.create(author=self.alice, task=self.published_task2, passed=True)

        for user in [self.bob, self.alice]:
            self.assertDictEqual(self.category1.completion_info(user), {
                'num_completed': 2,
                'num_published': 2,
                'is_completed': True,
                'progress': 100
            })


class CompletedByTests(SimpleAccountsData, TaskData, TestCase):
    def test_no_solutions(self):
        for user in [self.bob, self.alice]:
            self.assertEqual(len(Task.objects.completed_by(user)), 0)
            self.assertEqual(len(self.category1.task_set.completed_by(user)), 0)
            self.assertEqual(len(self.category2.task_set.completed_by(user)), 0)

    def test_only_failed_solutions(self):
        Solution.objects.create(author=self.bob, task=self.published_task1)
        Solution.objects.create(author=self.alice, task=self.published_task2)
        for user in [self.bob, self.alice]:
            self.assertEqual(len(Task.objects.completed_by(user)), 0)
            self.assertEqual(len(self.category1.task_set.completed_by(user)), 0)
            self.assertEqual(len(self.category2.task_set.completed_by(user)), 0)

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
        self.assertEqual(len(self.category2.task_set.not_completed_by(self.bob)), 0)

    def test_issue184(self):
        Solution.objects.create(author=self.bob, task=self.published_task1, passed=True)
        Solution.objects.create(author=self.alice, task=self.published_task1)

        self.assertEqual(len(self.category1.task_set.completed_by(self.bob)), 1)
        self.assertEqual(len(self.category1.task_set.not_completed_by(self.bob)), 3)
        self.assertEqual(len(self.category1.task_set.completed_by(self.alice)), 0)
        self.assertEqual(len(self.category1.task_set.not_completed_by(self.alice)), 4)
