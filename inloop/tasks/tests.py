from doctest import DocTestSuite
from os import makedirs, path, remove
from shutil import copy, rmtree, which

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files import File, base
from django.test import TestCase
from django.utils import timezone
from django.utils.text import slugify

from inloop.accounts.models import UserProfile
from inloop.tasks import models
from inloop.tasks.models import (Checker, CheckerResult, MissingTaskMetadata,
                                 Task, TaskCategory, TaskSolution,
                                 TaskSolutionFile)
from inloop.tasks.validators import validate_short_id

TEST_IMAGE_PATH = path.join(settings.INLOOP_ROOT, "tests", "test.jpg")
TEST_CLASS_PATH = path.join(settings.INLOOP_ROOT, "tests", "HelloWorld.java")
MEDIA_IMAGE_PATH = path.join(settings.MEDIA_ROOT, "test.jpg")
MEDIA_CLASS_PATH = path.join(settings.MEDIA_ROOT, "HelloWorld.java")
TEST_FAILURE_RESULT = """\
<?xml version="1.0" encoding="UTF-8"?>\r\n
<testsuite name="BasicTest" tests="2" skipped="0" failures="0" errors="0"
timestamp="2016-03-09T22:35:21" hostname="fde9bfd357e5" time="0.001">
<properties/>
<testcase name="testInstantiation" classname="BasicTest" time="0.0"/>
<testcase name="testToString" classname="BasicTest" time="0.0"/>
<system-out><![CDATA[]]></system-out>
<system-err><![CDATA[]]></system-err>
</testsuite>
<?xml version="1.0" encoding="UTF-8"?>\r\n
<testsuite name="AdvancedTest" tests="4" skipped="0" failures="1" errors="0"
timestamp="2016-03-09T22:35:21" hostname="fde9bfd357e5" time="0.007">
<properties/>
<testcase name="testAdd" classname="AdvancedTest" time="0.016">
<failure message="You fail!" type="java.lang.AssertionError">
HERE BE STACKTRACES
</failure>
</testcase>
<testcase name="testSubtract" classname="AdvancedTest" time="0.001"/>
<testcase name="testWhatever" classname="AdvancedTest" time="0.001"/>
<testcase name="testImportantStuff" classname="AdvancedTest" time="0.001"/>
<system-out><![CDATA[]]></system-out>
<system-err><![CDATA[]]></system-err>
</testsuite>""".encode("utf-8")
TEST_SUCCESS_RESULT = """\
<?xml version="1.0" encoding="UTF-8"?>\r\n
<testsuite name="BasicTest" tests="2" skipped="0" failures="0" errors="0"
timestamp="2016-03-09T22:35:21" hostname="fde9bfd357e5" time="0.001">
<properties/>
<testcase name="testInstantiation" classname="BasicTest" time="0.0"/>
<testcase name="testToString" classname="BasicTest" time="0.0"/>
<system-out><![CDATA[]]></system-out>
<system-err><![CDATA[]]></system-err>
</testsuite>
<?xml version="1.0" encoding="UTF-8"?>\r\n
<testsuite name="AdvancedTest" tests="4" skipped="0" failures="0" errors="0"
timestamp="2016-03-09T22:35:21" hostname="fde9bfd357e5" time="0.007">
<properties/>
<testcase name="testAdd" classname="AdvancedTest" time="0.004"/>
<testcase name="testSubtract" classname="AdvancedTest" time="0.001"/>
<testcase name="testWhatever" classname="AdvancedTest" time="0.001"/>
<testcase name="testImportantStuff" classname="AdvancedTest" time="0.001"/>
<system-out><![CDATA[]]></system-out>
<system-err><![CDATA[]]></system-err>
</testsuite>""".encode("utf-8")

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


class TaskModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        copy(TEST_IMAGE_PATH, MEDIA_IMAGE_PATH)

    @classmethod
    def tearDownClass(cls):
        remove(MEDIA_IMAGE_PATH)
        super().tearDownClass()

    def setUp(self):
        self.user = create_test_user()
        self.cat = create_task_category("Basic", MEDIA_IMAGE_PATH)
        self.t1 = create_test_task(author=self.user, category=self.cat, active=True)
        self.t2 = create_test_task(author=self.user, category=self.cat, active=False)

    def tearDown(self):
        remove(self.cat.image.path)

    def test_validate_short_id(self):
        with self.assertRaises(ValidationError):
            validate_short_id("ABC")
        with self.assertRaises(ValidationError):
            validate_short_id("abc")
        with self.assertRaises(ValidationError):
            validate_short_id("1a")
        with self.assertRaises(ValidationError):
            validate_short_id("1ab")
        with self.assertRaises(ValidationError):
            validate_short_id("1$")
        self.assertIsNone(validate_short_id("ab"))
        self.assertIsNone(validate_short_id("Ab"))
        self.assertIsNone(validate_short_id("AB"))
        self.assertIsNone(validate_short_id("A1"))

    def test_task_is_active(self):
        self.assertTrue(self.t1.is_active())
        self.assertFalse(self.t2.is_active())

    def test_disabled_task_not_displayed_in_index(self):
        self.client.login(username=self.user.username, password="123456")
        resp = self.client.get("/", follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(self.t2.title in resp.content.decode())

    def test_invalid_inputs(self):
        with self.assertRaises(ValidationError):
            Task.objects.create(publication_date="abc")

        with self.assertRaises(ValidationError):
            Task.objects.create(deadline_date="abc")

    def test_task_location(self):
        subpath = "inloop/media/exercises/"
        self.assertTrue(subpath + self.t1.slug in self.t1.task_location())  # activated
        self.assertTrue(subpath + self.t2.slug in self.t2.task_location())  # deactivated


class TaskCategoryTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        copy(TEST_IMAGE_PATH, MEDIA_IMAGE_PATH)

    @classmethod
    def tearDownClass(cls):
        remove(MEDIA_IMAGE_PATH)
        super().tearDownClass()

    def setUp(self):
        cat_name = "Whitespace here and 123 some! TABS \t - \"abc\" (things)\n"
        self.user = create_test_user()
        self.cat = create_task_category(cat_name, MEDIA_IMAGE_PATH)
        self.task = create_test_task(author=self.user, category=self.cat)
        self.ts = create_test_task_solution(author=self.user, task=self.task, passed=True)

    def tearDown(self):
        remove(self.cat.image.path)

    def test_image_path(self):
        p = TaskCategory.objects.get(pk=1).image.path
        with open(p, "rb") as fd:
            self.assertTrue(fd, "Image file not found")

    def test_slugify_on_save(self):
        self.assertEqual(self.cat.short_id, "whitespace-here-and-123-some-tabs-abc-things")

    def test_get_tuple(self):
        slug = "whitespace-here-and-123-some-tabs-abc-things"
        name = "Whitespace here and 123 some! TABS \t - \"abc\" (things)\n"
        self.assertEqual(self.cat.get_tuple(), (slug, name))

    def test_completed_tasks_for_user(self):
        self.assertEqual(self.cat.completed_tasks_for_user(self.user)[0], self.task)

    def test_completed_tasks_empty_category(self):
        empty_cat = create_task_category("empty", TEST_IMAGE_PATH)
        self.assertFalse(empty_cat.completed_tasks_for_user(self.user).exists())
        remove(empty_cat.image.path)

    def test_completed_tasks_uncompleted(self):
        self.ts.passed = False
        self.ts.save()
        self.assertFalse(self.cat.completed_tasks_for_user(self.user).exists())


class TaskSolutionTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        copy(TEST_IMAGE_PATH, MEDIA_IMAGE_PATH)
        copy(TEST_CLASS_PATH, MEDIA_CLASS_PATH)

    @classmethod
    def tearDownClass(cls):
        remove(MEDIA_IMAGE_PATH)
        remove(MEDIA_CLASS_PATH)
        rmtree(path.join(settings.MEDIA_ROOT, "solutions", "test_user"))
        super().tearDownClass()

    def setUp(self):
        self.user = create_test_user()
        self.cat = create_task_category("Basic", MEDIA_IMAGE_PATH)
        self.task = create_test_task(author=self.user, category=self.cat, active=True)
        self.ts = create_test_task_solution(author=self.user, task=self.task)
        self.tsf = create_test_task_solution_file(solution=self.ts, contentpath=MEDIA_CLASS_PATH)

        CheckerResult.objects.create(
            solution=self.ts,
            result="",
            time_taken=13.37,
            passed=False
        )

    def tearDown(self):
        remove(self.cat.image.path)

    def test_default_value(self):
        self.assertFalse(self.ts.passed)

    def test_get_upload_path(self):
        self.assertRegex(
            models.get_upload_path(self.tsf, self.tsf.filename),
            (r"solutions/test_user/active-task/"
             "[\d]{4}/[\d]{2}/[\d]{2}/[\d]{2}_[\d]{1,2}_[\d]+/[\w]+.java")
        )


class CheckerTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        copy(TEST_IMAGE_PATH, MEDIA_IMAGE_PATH)
        copy(TEST_CLASS_PATH, MEDIA_CLASS_PATH)

    @classmethod
    def tearDownClass(cls):
        remove(MEDIA_IMAGE_PATH)
        remove(MEDIA_CLASS_PATH)
        super().tearDownClass()

    def setUp(self):
        self.user = create_test_user()
        self.cat = create_task_category("Basic", MEDIA_IMAGE_PATH)
        self.task = create_test_task(author=self.user, category=self.cat, active=True)
        self.ts = create_test_task_solution(author=self.user, task=self.task)
        self.tsf = create_test_task_solution_file(solution=self.ts, contentpath=MEDIA_CLASS_PATH)
        self.c = Checker(self.ts)

    def tearDown(self):
        remove(self.cat.image.path)

    def test_docker_present_on_system(self):
        self.assertIsNotNone(which("docker"), "Docker is not available on your system.")

    def test_generate_container_name_format(self):
        self.assertRegex(
            self.c._generate_container_name(),
            "-".join([self.user.username, self.task.slug, "[\\w]{21}"])
        )

    def test_correct_parse_result(self):
        self.c._parse_result(result=TEST_SUCCESS_RESULT, compiler_error=False)
        cr = CheckerResult.objects.get(solution=self.ts)
        self.assertTrue(cr.passed)
        self.assertTrue(TaskSolution.objects.get(pk=self.ts.pk).passed)
        self.assertEqual(cr.time_taken, 0.01)
        self.assertEqual(cr.result, TEST_SUCCESS_RESULT.decode())

    def test_failure_parse_result(self):
        self.c._parse_result(result=TEST_FAILURE_RESULT, compiler_error=False)
        cr = CheckerResult.objects.get(solution=self.ts)
        self.assertFalse(cr.passed)
        self.assertFalse(TaskSolution.objects.get(pk=self.ts.pk).passed)
        self.assertEqual(cr.time_taken, 0.01)
        self.assertEqual(cr.result, TEST_FAILURE_RESULT.decode())

    def test_compiler_failure_parse_result(self):
        self.c._parse_result(result="compiler trace", compiler_error=True)
        cr = CheckerResult.objects.get(solution=self.ts)
        self.assertFalse(cr.passed)
        self.assertFalse(TaskSolution.objects.get(pk=self.ts.pk).passed)
        self.assertEqual(cr.time_taken, 0.0)
        self.assertEqual(cr.result, "compiler trace")

    def test_empty_result_parse_result(self):
        self.c._parse_result(result="", compiler_error=False)
        cr = CheckerResult.objects.get(solution=self.ts)
        self.assertEqual(cr.result, "For some reason I didn't get anything.. What are you doing?")


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
