import os
import shutil
from os import path

from django.conf import settings
from django.core.files.base import ContentFile
from django.test import TestCase
from django.utils import timezone
from django.utils.text import slugify

from inloop.accounts.models import UserProfile
from inloop.tasks.models import Task, TaskCategory, TaskSolution, TaskSolutionFile


TEST_IMAGE_PATH = path.join(settings.INLOOP_ROOT, "tests", "test.jpg")
TEST_CLASS_PATH = path.join(settings.INLOOP_ROOT, "tests", "HelloWorld.java")
MEDIA_IMAGE_PATH = path.join(settings.MEDIA_ROOT, "test.jpg")
MEDIA_CLASS_PATH = path.join(settings.MEDIA_ROOT, "HelloWorld.java")


class TasksTestBase(TestCase):
    """
    Abstract base class which unifies some common test setup tasks.
    """
    category_defaults = {
        "name": "Basic",
    }

    task_defaults = {
        "title": "Published task",
        "name": "PublishedTask",
        "publication_date": timezone.now(),
        "deadline_date": timezone.now() + timezone.timedelta(days=2),
        "description": "# Heading\nSome text.\n"
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        shutil.copy(TEST_IMAGE_PATH, MEDIA_IMAGE_PATH)
        shutil.copy(TEST_CLASS_PATH, MEDIA_CLASS_PATH)

    @classmethod
    def tearDownClass(cls):
        os.remove(MEDIA_IMAGE_PATH)
        os.remove(MEDIA_CLASS_PATH)
        super().tearDownClass()

    def setUp(self):
        self.user = self.create_user("Chuck Norris")
        self.cat = self.create_category()
        self.task = self.create_task()

    def create_user(self, name):
        first_name, last_name = name.split()
        username = "%s_%s" % (first_name, last_name)
        email = "%s.%s@example.org" % (first_name, last_name)

        return UserProfile.objects.create_user(
            username=username.lower(),
            first_name=first_name,
            last_name=last_name,
            email=email.lower(),
            password="s3cret",
            mat_num="1234567"
        )

    def create_category(self, **kwargs):
        for k, v in self.category_defaults.items():
            kwargs.setdefault(k, v)
        return TaskCategory.objects.create(**kwargs)

    def create_task(self, **kwargs):
        kwargs.setdefault("author", self.user)
        kwargs.setdefault("category", self.cat)
        for k, v in self.task_defaults.items():
            kwargs.setdefault(k, v)
        # FIXME: the model should slugify this, not me
        kwargs["slug"] = slugify(kwargs["title"])
        return Task.objects.create(**kwargs)

    def create_solution(self, **kwargs):
        kwargs.setdefault("author", self.user)
        kwargs.setdefault("task", self.task)
        return TaskSolution.objects.create(**kwargs)

    def create_solution_file(self, solution, contentpath=MEDIA_CLASS_PATH):
        # FIXME: basename should be figured out by SolutionFile
        filename = path.basename(contentpath)
        tsf = TaskSolutionFile.objects.create(
            solution=solution,
            filename=filename,
            file=None
        )
        # FIXME: file handling -- is this supposed to work this way?
        with open(contentpath, encoding="utf-8") as f:
            tsf.file.save(filename, ContentFile(f.read()))
        return tsf

    def test_selftest(self):
        """Test if the test data was wired up correctly."""
        self.assertEqual(self.user.username, "chuck_norris")
        self.assertEqual(self.user.email, "chuck.norris@example.org")
        self.assertEqual(self.cat.name, self.category_defaults["name"])
        self.assertEqual(self.task.author, self.user)
        self.assertEqual(self.task.category, self.cat)
