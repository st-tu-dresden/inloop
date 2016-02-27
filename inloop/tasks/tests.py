from os import path
from doctest import DocTestSuite
from unittest import skip

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


class TaskModelTests(TestCase):
    def setUp(self):
        self.password = '123456'
        author = UserProfile.objects.create_user(
            username='test_user',
            first_name='first_name',
            last_name='last_name',
            email='test@example.com',
            password=self.password,
            mat_num='0000000')

        UserProfile.objects.create_superuser(
            username='superuser',
            email='staff@example.com',
            password=self.password,
            first_name='first_name',
            last_name='last_name',
            mat_num='1234567')

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
        self.client.login(username=user.username, password=self.password)
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

    @skip
    def test_superuser_can_edit_task(self):
        task = Task.objects.get(title='active_task')
        superuser = UserProfile.objects.get(username='superuser')
        url = '/tasks/' + task.slug + '/edit/'
        new_title = 'New title'
        new_desc = 'New description'
        new_pub = timezone.now() - timezone.timedelta(days=1)
        new_dead = timezone.now() + timezone.timedelta(days=7)
        new_cat = TaskCategory.objects.create(
            short_id='LE',
            name='Lesson'
        )

        self.client.login(username=superuser.username, password=self.password)
        # edit form accessible
        resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        # post new content
        data_dict = {
            'e_title': new_title,
            'e_desc': new_desc,
            'e_pub_date': new_pub.strftime('%m/%d/%Y %H:%M'),
            'e_dead_date': new_dead.strftime('%m/%d/%Y %H:%M'),
            'e_cat': new_cat
        }
        resp = self.client.post(url, data_dict, follow=True)
        task = Task.objects.get(title=new_title)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(task.title, new_title)
        self.assertEqual(task.description, new_desc)
        self.assertEqual(task.publication_date.strftime('%m/%d/%Y %H:%M'),
                         new_pub.strftime('%m/%d/%Y %H:%M'))
        self.assertEqual(task.deadline_date.strftime('%m/%d/%Y %H:%M'),
                         new_dead.strftime('%m/%d/%Y %H:%M'))
        self.assertEqual(task.category, new_cat)


class TaskCategoryTests(TestCase):
    def setUp(self):
        self.user = UserProfile.objects.create_user(
            username='test_user',
            first_name='first_name',
            last_name='last_name',
            email='test@example.com',
            password='123456',
            mat_num='0000000'
        )
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
        self.password = '123456'

        author = UserProfile.objects.create_user(
            username='test_user',
            first_name='first_name',
            last_name='last_name',
            email='test@example.com',
            password=self.password,
            mat_num='0000000')

        UserProfile.objects.create_superuser(
            username='superuser',
            email='staff@example.com',
            password=self.password,
            first_name='first_name',
            last_name='last_name',
            mat_num='1234567')

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
