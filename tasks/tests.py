from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from tasks.models import Task


class TaskModelests(TestCase):

    def setUp(self):
        Task.objects.create(
            title='active_task',
            author='unittest',
            description='',
            publication_date=timezone.now() - timezone.timedelta(days=2),
            deadline_date=timezone.now() + timezone.timedelta(days=2),
            category='B',
            slug='active-task'
        )

        Task.objects.create(
            title='disabled_task',
            author='unittest',
            description='',
            publication_date=timezone.now() + timezone.timedelta(days=1),
            deadline_date=timezone.now() + timezone.timedelta(days=5),
            category='B',
            slug='disabled-task'
        )

    def test_task_is_active(self):
        active_task = Task.objects.get(title='active_task')
        disabled_task = Task.objects.get(title='disabled_task')

        self.assertTrue(active_task.is_active())
        self.assertFalse(disabled_task.is_active())

    def test_invalid_inputs(self):
        with self.assertRaises(ValidationError):
            Task.objects.create(publication_date='abc')

        with self.assertRaises(ValidationError):
            Task.objects.create(deadline_date='abc')
