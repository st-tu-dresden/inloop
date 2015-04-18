from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from accounts.models import UserProfile
from tasks.models import Task, TaskCategory


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

        basic = TaskCategory.objects.create(
            short_id='BA',
            name='Basic'
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
        self.assertFalse(disabled_task.title in resp.content)

    def test_invalid_inputs(self):
        with self.assertRaises(ValidationError):
            Task.objects.create(publication_date='abc')

        with self.assertRaises(ValidationError):
            Task.objects.create(deadline_date='abc')

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
