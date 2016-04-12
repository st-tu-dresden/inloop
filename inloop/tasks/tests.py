from doctest import DocTestSuite
from os import makedirs, path

from django.conf import settings
from django.core.exceptions import ValidationError

from django.core.files import File, base
from django.test import TestCase
from django.utils import timezone
from django.utils.text import slugify

from inloop.accounts.models import UserProfile
from inloop.tasks import models
from inloop.tasks.models import (CheckerResult, MissingTaskMetadata, Task,
                                 TaskCategory, TaskSolution, TaskSolutionFile)
from inloop.tasks.test_base import TasksTestBase

TEST_IMAGE_PATH = path.join(settings.INLOOP_ROOT, "tests", "test.jpg")
TEST_CLASS_PATH = path.join(settings.INLOOP_ROOT, "tests", "HelloWorld.java")
MEDIA_IMAGE_PATH = path.join(settings.MEDIA_ROOT, "test.jpg")
MEDIA_CLASS_PATH = path.join(settings.MEDIA_ROOT, "HelloWorld.java")

if not path.exists(settings.MEDIA_ROOT):
    makedirs(settings.MEDIA_ROOT)


def load_tests(loader, tests, ignore):
    """Initialize doctests for this module."""
    tests.addTests(DocTestSuite(models))
    return tests


def create_task_category(name, image):
    cat = TaskCategory(name=name)
    with open(image, "rb") as fd:
        cat.image = File(fd)
        cat.save()
    return cat


def create_test_user(username="test_user", first_name="first_name", last_name="last_name",
                     email="test@example.com", password="123456", mat_num="0000000"):
        return UserProfile.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            mat_num=mat_num)


def create_test_task(author, category, description="", pub_date=None, dead_date=None,
                     title=None, active=True):
    if active:
        title = "Active Task" if not title else title
        pub_date = timezone.now() - timezone.timedelta(days=2) if not pub_date else pub_date
        dead_date = timezone.now() + timezone.timedelta(days=2) if not dead_date else dead_date
    else:
        title = "Disabled Task" if not title else title
        pub_date = timezone.now() + timezone.timedelta(days=1)
        dead_date = timezone.now() + timezone.timedelta(days=5)

    return Task.objects.create(
        title=title,
        author=author,
        description=description,
        publication_date=pub_date,
        deadline_date=dead_date,
        category=category,
        slug=slugify(title))


def create_test_task_solution(author, task, sub_date=None, passed=False):
    return TaskSolution.objects.create(
        submission_date=timezone.now() - timezone.timedelta(days=1) if not sub_date else sub_date,
        author=author,
        task=task,
        passed=passed
    )


def create_test_task_solution_file(solution, contentpath):
    filename = path.basename(contentpath)
    tsf = TaskSolutionFile.objects.create(
        solution=solution,
        filename=filename,
        file=None
    )
    with open(contentpath, encoding="utf-8") as f:
        tsf.file.save(filename, base.ContentFile(f.read()))
    return tsf


class TaskModelTests(TasksTestBase):
    def setUp(self):
        super().setUp()
        self.inactive_task = self.create_task(
            title="Inactive task",
            publication_date=timezone.now() + timezone.timedelta(days=2)
        )

    def test_task_is_active(self):
        self.assertTrue(self.task.is_active())
        self.assertFalse(self.inactive_task.is_active())

    def test_disabled_task_not_displayed_in_index(self):
        self.client.login(
            username=self.user_defaults["username"],
            password=self.user_defaults["password"]
        )
        response = self.client.get("/", follow=True)
        self.assertNotContains(response, self.inactive_task.title)

    def test_invalid_inputs(self):
        with self.assertRaises(ValidationError):
            Task.objects.create(publication_date="abc")

        with self.assertRaises(ValidationError):
            Task.objects.create(deadline_date="abc")

    def test_task_location(self):
        subpath = "inloop/media/exercises/%s"
        self.assertIn(subpath % self.task.slug, self.task.task_location())
        self.assertIn(subpath % self.inactive_task.slug, self.inactive_task.task_location())


class TaskCategoryTests(TasksTestBase):
    def test_slugify_on_save(self):
        cat_name = "Whitespace here and 123 some! TABS \t - \"abc\" (things)\n"
        slug = "whitespace-here-and-123-some-tabs-abc-things"
        category = self.create_category(name=cat_name)
        self.assertEqual(category.short_id, slug)
        self.assertEqual(category.get_tuple(), (slug, cat_name))

    def test_completed_tasks_empty_category(self):
        empty_cat = self.create_category(name="empty")
        self.assertFalse(empty_cat.completed_tasks_for_user(self.user).exists())

    def test_tasks_uncompleted(self):
        solution = self.create_solution()
        self.assertFalse(solution.passed)
        self.assertFalse(self.cat.completed_tasks_for_user(self.user).exists())

    def test_tasks_completed_multiple_solutions(self):
        solution1 = self.create_solution(passed=True)
        solution2 = self.create_solution(passed=True)
        self.assertTrue(solution1.passed)
        self.assertTrue(solution2.passed)
        self.assertEqual(self.cat.completed_tasks_for_user(self.user).count(), 1)
        self.assertEqual(self.cat.completed_tasks_for_user(self.user)[0], self.task)

        task2 = self.create_task(title="Another task")
        solution3 = self.create_solution(task=task2)
        self.assertFalse(solution3.passed)
        self.assertEqual(self.cat.completed_tasks_for_user(self.user).count(), 1)

        solution4 = self.create_solution(task=task2, passed=True)
        self.assertTrue(solution4.passed)
        self.assertEqual(self.cat.completed_tasks_for_user(self.user).count(), 2)


class TaskSolutionTests(TasksTestBase):
    def test_default_value(self):
        solution = self.create_solution()
        result = CheckerResult.objects.create(solution=solution)
        self.assertFalse(result.passed)

    def test_get_upload_path(self):
        solution = self.create_solution()
        tsf = self.create_solution_file(solution=solution)
        self.assertRegex(
            models.get_upload_path(tsf, tsf.filename),
            (r"solutions/chuck_norris/active-task/"
             "[\d]{4}/[\d]{2}/[\d]{2}/[\d]{2}_[\d]{1,2}_[\d]+/HelloWorld.java")
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
        self.valid_json = {"title": "Test title", "category": "Lesson",
                           "pubdate": "2015-05-01 13:37:00"}

    def test_validate_empty(self):
        with self.assertRaises(MissingTaskMetadata) as cm:
            self.manager._validate(dict())
        actual = set(cm.exception.args[0])
        expected = {"title", "category", "pubdate"}
        self.assertEqual(actual, expected)

    def test_validate_valid(self):
        self.manager._validate(self.valid_json)

    def test_update(self):
        input = Task()
        task = self.manager._update_task(input, self.valid_json)

        self.assertIs(task, input)
        self.assertEqual(task.title, "Test title")
        self.assertEqual(task.slug, "test-title")
        self.assertEqual(task.category.name, "Lesson")

        pubdate = task.publication_date.strftime("%Y-%m-%d %H:%M:%S")
        self.assertEqual(pubdate, self.valid_json["pubdate"])

    def test_save_task_with_valid_json(self):
        task = Task.objects.get_or_create_json(self.valid_json, "Test title")
        task.save()
