from os import path
from doctest import DocTestSuite

from django.core.exceptions import ValidationError
from django.core.files import File
from django.test import TestCase
from django.utils import timezone
from django.conf import settings

from inloop.accounts.models import UserProfile
from inloop.tasks import models
from inloop.tasks.models import (MissingTaskMetadata, Task, TaskCategory,
                                 TaskSolution, TaskSolutionFile, CheckerResult)

TEST_IMAGE = path.join(settings.INLOOP_ROOT, 'tests', 'test.jpg')


def load_tests(loader, tests, ignore):
    """Initialize doctests for this module."""
    tests.addTests(DocTestSuite(models))
    return tests


def create_task_category(name, image):
    cat = TaskCategory(name=name)
    with open(image, 'rb') as fd:
        cat.image = File(fd)
        cat.save()
    return cat


def create_test_user(username='test_user', first_name='first_name', last_name='last_name',
                     email='test@example.com', password='123456', mat_num='0000000'):
        return UserProfile.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            mat_num=mat_num)


class TaskModelTests(TestCase):
    def setUp(self):
        author = create_test_user()

        self.basic = create_task_category('Basic', TEST_IMAGE)

        self.t1 = Task.objects.create(
            title='active_task',
            author=author,
            description='',
            publication_date=timezone.now() - timezone.timedelta(days=2),
            deadline_date=timezone.now() + timezone.timedelta(days=2),
            category=self.basic,
            slug='active-task')

        self.t2 = Task.objects.create(
            title='disabled_task',
            author=author,
            description='',
            publication_date=timezone.now() + timezone.timedelta(days=1),
            deadline_date=timezone.now() + timezone.timedelta(days=5),
            category=self.basic,
            slug='disabled-task')

    def test_task_is_active(self):
        active_task = Task.objects.get(title='active_task')
        disabled_task = Task.objects.get(title='disabled_task')

        self.assertTrue(active_task.is_active())
        self.assertFalse(disabled_task.is_active())

    def test_disabled_task_not_displayed_in_index(self):
        user = UserProfile.objects.get(username='test_user')
        disabled_task = Task.objects.get(title='disabled_task')
        self.client.login(username=user.username, password='123456')
        resp = self.client.get('/', follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(disabled_task.title in resp.content.decode())

    def test_invalid_inputs(self):
        with self.assertRaises(ValidationError):
            Task.objects.create(publication_date='abc')

        with self.assertRaises(ValidationError):
            Task.objects.create(deadline_date='abc')

    def test_task_location(self):
        subpath = 'inloop/media/exercises/'
        self.assertTrue(subpath + self.t1.slug in self.t1.task_location())  # activated
        self.assertTrue(subpath + self.t2.slug in self.t2.task_location())  # deactivated


class TaskCategoryTests(TestCase):
    def setUp(self):
        self.user = create_test_user()
        name = 'Whitespace here and 123 some! TABS \t - "abc" (things)\n'
        self.cat = create_task_category(name, TEST_IMAGE)
        self.task = Task.objects.create(
            title='active_task',
            author=self.user,
            description='',
            publication_date=timezone.now() - timezone.timedelta(days=2),
            deadline_date=timezone.now() + timezone.timedelta(days=2),
            category=self.cat,
            slug='active-task')
        self.ts = TaskSolution.objects.create(
            submission_date=timezone.now() - timezone.timedelta(days=1),
            author=self.user,
            task=self.task,
            passed=True
        )

    def test_image_path(self):
        p = TaskCategory.objects.get(pk=1).image.path
        with open(p, 'rb') as fd:
            self.assertTrue(fd, 'Image file not found')

    def test_slugify_on_save(self):
        self.assertEqual(self.cat.short_id, 'whitespace-here-and-123-some-tabs-abc-things')

    def test_str(self):
        self.assertEqual(str(self.cat), 'whitespace-here-and-123-some-tabs-abc-things')

    def test_get_tuple(self):
        slug = 'whitespace-here-and-123-some-tabs-abc-things'
        name = 'Whitespace here and 123 some! TABS \t - "abc" (things)\n'
        self.assertEqual(self.cat.get_tuple(), (slug, name))

    def test_completed_tasks_for_user(self):
        self.assertEqual(self.cat.completed_tasks_for_user(self.user)[0], self.task)

    def test_completed_tasks_empty_category(self):
        empty_cat = create_task_category('empty', TEST_IMAGE)
        self.assertFalse(empty_cat.completed_tasks_for_user(self.user).exists())

    def test_completed_tasks_uncompleted(self):
        self.ts.passed = False
        self.ts.save()
        self.assertFalse(self.cat.completed_tasks_for_user(self.user).exists())


class TaskSolutionTests(TestCase):
    def setUp(self):
        author = create_test_user()

        self.basic = create_task_category('Basic', TEST_IMAGE)

        t1 = Task.objects.create(
            title='active_task',
            author=author,
            description='',
            publication_date=timezone.now() - timezone.timedelta(days=2),
            deadline_date=timezone.now() + timezone.timedelta(days=2),
            category=self.basic,
            slug='active-task')

        ts1 = TaskSolution.objects.create(
            submission_date=timezone.now() - timezone.timedelta(days=1),
            author=author,
            task=t1
        )

        self.tsf = TaskSolutionFile.objects.create(
            solution=ts1,
            filename='foo.java',
            file=None
        )

        CheckerResult.objects.create(
            solution=ts1,
            result='',
            time_taken=13.37,
            passed=False
        )

    def test_default_value(self):
        sol = TaskSolution.objects.get(pk=1)
        self.assertFalse(sol.passed)

    def test_get_upload_path(self):
        self.assertRegex(
            models.get_upload_path(self.tsf, self.tsf.filename),
            (r'solutions/test_user/active-task/'
             '[\d]{4}/[\d]{2}/[\d]{2}/[\d]{2}_[\d]{1,2}_[\d]+/[\w]+.java')
        )


class TaskCategoryManagerTests(TestCase):
    def setUp(self):
        TaskCategory.objects.create(name="Test category")

    def test_returns_existing_category(self):
        self.assertEqual(TaskCategory.objects.count(), 1)
        category = TaskCategory.objects.get_or_create("Test category")
        self.assertEqual(category.name, "Test category")
        self.assertEqual(TaskCategory.objects.count(), 1)

    def test_returns_new_category(self):
        self.assertEqual(TaskCategory.objects.count(), 1)
        category = TaskCategory.objects.get_or_create("Another category")
        self.assertEqual(category.name, "Another category")
        self.assertEqual(TaskCategory.objects.count(), 2)


class TaskManagerTests(TestCase):
    def setUp(self):
        self.manager = Task.objects
        self.valid_json = {'title': 'Test title', 'category': 'Lesson',
                           'pubdate': '2015-05-01 13:37:00'}

    def test_validate_empty(self):
        with self.assertRaises(MissingTaskMetadata) as cm:
            self.manager._validate(dict())
        actual = set(cm.exception.args[0])
        expected = {'title', 'category', 'pubdate'}
        self.assertEqual(actual, expected)

    def test_validate_valid(self):
        self.manager._validate(self.valid_json)

    def test_update(self):
        input = Task()
        task = self.manager._update_task(input, self.valid_json)

        self.assertIs(task, input)
        self.assertEqual(task.title, 'Test title')
        self.assertEqual(task.slug, 'test-title')
        self.assertEqual(task.category.name, 'Lesson')

        pubdate = task.publication_date.strftime('%Y-%m-%d %H:%M:%S')
        self.assertEqual(pubdate, self.valid_json['pubdate'])

    def test_save_task_with_valid_json(self):
        task = Task.objects.get_or_create_json(self.valid_json, "Test title")
        task.save()
