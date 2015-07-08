from os import path
from unittest import skip

from django.core.exceptions import ValidationError
from django.core.files import File
from django.test import TestCase
from django.utils import timezone
from django.conf import settings

from accounts.models import UserProfile
from tasks.models import Task, TaskCategory, TaskSolution, TaskSolutionFile


TEST_IMAGE = path.join(settings.BASE_DIR, 'tests', 'test.jpg')


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

        with open(TEST_IMAGE, 'rb') as fd:
            basic = TaskCategory.objects.create(
                short_id='BA',
                name='Basic',
                image=File(fd)
            )

        Task.objects.create(
            title='active_task',
            author=author,
            description='',
            publication_date=timezone.now() - timezone.timedelta(days=2),
            deadline_date=timezone.now() + timezone.timedelta(days=2),
            category=basic,
            slug='active-task')

        Task.objects.create(
            title='disabled_task',
            author=author,
            description='',
            publication_date=timezone.now() + timezone.timedelta(days=1),
            deadline_date=timezone.now() + timezone.timedelta(days=5),
            category=basic,
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
    def test_image_path(self):
        cat = TaskCategory(name='Unittest')
        with open(TEST_IMAGE, 'rb') as fd:
            cat.image = File(fd)
            cat.save()

        p = TaskCategory.objects.get(pk=1).image.path
        with open(p, 'rb') as fd:
            self.assertTrue(fd, 'Image file not found')


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

        with open(TEST_IMAGE, 'rb') as fd:
            basic = TaskCategory.objects.create(
                short_id='BA',
                name='Basic',
                image=File(fd)
            )

        t1 = Task.objects.create(
            title='active_task',
            author=author,
            description='',
            publication_date=timezone.now() - timezone.timedelta(days=2),
            deadline_date=timezone.now() + timezone.timedelta(days=2),
            category=basic,
            slug='active-task')

        ts1 = TaskSolution.objects.create(
            submission_date=timezone.now() - timezone.timedelta(days=1),
            author=author,
            task=t1
            # omit is_correct as default = False
        )

        TaskSolutionFile.objects.create(
            solution=ts1,
            filename='foo.java',
            file=None
        )

        TaskSolutionFile.objects.create(
            solution=ts1,
            filename='bar.java',
            file=None
        )

        TaskSolutionFile.objects.create(
            solution=ts1,
            filename='baz.java',
            file=None
        )

    def test_default_value(self):
        sol = TaskSolution.objects.get(pk=1)
        self.assertFalse(sol.is_correct)
