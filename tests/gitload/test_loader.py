from unittest.mock import patch

from django.test import TestCase

from inloop.gitload.loader import InvalidTask, load_task, load_tasks, parse_metafile
from inloop.gitload.repo import Repository
from inloop.tasks.models import Category, FileTemplate, Task

from . import TESTREPO_PATH


class TaskLoadTest(TestCase):
    @patch("inloop.gitload.loader.repository_loaded")
    @patch("inloop.gitload.loader.LOG")
    def test_load_tasks(self, mocked_logger, mocked_signal):
        load_tasks(Repository(TESTREPO_PATH))
        mocked_signal.send.assert_called_once()
        self.assertEqual(3, mocked_logger.error.call_count)

    def test_load_task(self):
        self.assertEqual(0, len(Task.objects.all()))
        load_task(TESTREPO_PATH.joinpath("task1/task.md"))
        self.assertEqual(1, len(Task.objects.all()))
        task = Task.objects.first()
        self.assertEqual("Task 1", task.title)

    def test_load_task_creates_category(self):
        self.assertEqual(0, len(Category.objects.all()))
        load_task(TESTREPO_PATH.joinpath("task1/task.md"))
        self.assertEqual(1, len(Category.objects.all()))
        task = Task.objects.first()
        self.assertEqual("Test Category", task.category.name)

    def test_load_task_that_already_exists(self):
        category = Category.objects.create(name="Old Category")
        Task.objects.create(
            system_name="task1",
            title="Old Title",
            pubdate="2018-01-01 08:15:00Z",
            category=category,
        )
        load_task(TESTREPO_PATH.joinpath("task1/task.md"))
        self.assertEqual(1, len(Task.objects.all()))
        task = Task.objects.first()
        self.assertEqual("Task 1", task.title)
        self.assertEqual("Test Category", task.category.name)

    def test_disabled_task_not_loaded(self):
        self.assertEqual(0, len(Task.objects.all()))
        load_task(TESTREPO_PATH.joinpath("task2_disabled/task.md"))
        self.assertEqual(0, len(Task.objects.all()))

    def test_load_task_with_incomplete_meta(self):
        with self.assertRaises(InvalidTask) as context:
            load_task(TESTREPO_PATH.joinpath("task3_invalid/task.md"))
        self.assertIn("missing required field 'title'", str(context.exception))

    def test_parse_missing_metafile(self):
        with self.assertRaises(InvalidTask) as context:
            parse_metafile(TESTREPO_PATH.joinpath("task4_invalid"))
        self.assertIn("missing meta.json", str(context.exception))

    def test_parse_invalid_metafile(self):
        with self.assertRaises(InvalidTask) as context:
            parse_metafile(TESTREPO_PATH.joinpath("task5_invalid"))
        self.assertIn("malformed meta.json", str(context.exception))

    def test_deletes_previous_templates(self):
        category = Category.objects.create(name="Test Category")
        task = Task.objects.create(
            system_name="task1", title="Task 1", pubdate="2018-01-01 08:15:00Z", category=category
        )
        FileTemplate.objects.create(task=task, name="Foo.java", contents="Foo")
        self.assertEqual(1, len(FileTemplate.objects.all()))
        load_task(TESTREPO_PATH.joinpath("task1/task.md"))
        self.assertEqual(0, len(FileTemplate.objects.all()))

    def test_imports_templates_if_available(self):
        self.assertEqual(0, len(Task.objects.all()))
        self.assertEqual(0, len(FileTemplate.objects.all()))
        load_task(TESTREPO_PATH.joinpath("task6/task.md"))
        self.assertEqual(1, len(Task.objects.all()))
        templates = FileTemplate.objects.filter(task=Task.objects.first())
        self.assertEqual(1, len(templates))
        self.assertEqual("Example.java", templates[0].name)
        self.assertEqual("/* example */\n", templates[0].contents)
