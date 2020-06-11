import json
from datetime import datetime
from http import HTTPStatus
from json import JSONDecodeError

from django.contrib.auth import get_user_model
from django.core.exceptions import FieldError, ValidationError
from django.db.models import functions
from django.test import TestCase
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.utils.timezone import make_aware

from inloop.solutions.models import Solution
from inloop.statistics.forms import ALLOWED_TRUNCATOR_IDENTIFIERS, validate_granularity
from inloop.statistics.views import bad_request, queryset_limit_reached
from inloop.tasks.models import Category, Task

User = get_user_model()


class TruncatorAvailabilityTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Create a solution with the corresponding objects."""
        super().setUpClass()
        cls.category = Category.objects.create(id=1337, name="Test Category")
        cls.task = Task.objects.create(
            pubdate='2000-01-01 00:00Z',
            category_id=1337,
            title='Fibonacci',
            slug='task'
        )
        cls.author = User.objects.create_user(
            username='author',
            email='author@example.org',
            password='secret'
        )
        cls.solution = Solution.objects.create(
            author=cls.author,
            task=cls.task,
            passed=True
        )

    def test_allowed_truncator_identifiers(self):
        """Validate that all allowed truncator identifiers are supported by the backend."""
        field_name = 'submission_date'
        for identifier in ALLOWED_TRUNCATOR_IDENTIFIERS:
            trunc = functions.Trunc(field_name, identifier)
            try:
                queryset = Solution.objects.annotate(alias=trunc)
            except FieldError:
                self.fail(f'The {field_name} field is unavailable.')
            except ValueError:
                self.fail(f'The truncator identifier {identifier} is unavailable.')
            self.assertTrue(queryset, 'The fetched queryset should not be empty.')


class ValidatorTest(TestCase):
    def test_validate_granularity(self):
        """Test the granularity validator."""
        with self.assertRaises(ValidationError):
            validate_granularity('lightyears')
        for valid_value in ALLOWED_TRUNCATOR_IDENTIFIERS:
            try:
                validate_granularity(valid_value)
            except ValidationError:
                self.fail(f'The granularity validator should accept {valid_value}!')


class BadRequestTest(TestCase):
    def test_bad_request(self):
        reason = 'test_reason'
        response = bad_request(reason)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        content = response.content.decode()
        try:
            json_content = json.loads(content)
        except JSONDecodeError:
            self.fail('The response content could not be loaded.')
        self.assertEqual(json_content.get('reason'), reason)


class QuerysetLimitReachedTest(TestCase):
    def test_queryset_limit_reached(self):
        """Test the queryset limit reached response."""
        reason = 'test_reason'
        queryset_count = 100
        response = queryset_limit_reached(queryset_count, reason=reason)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        content = response.content.decode()
        try:
            json_content = json.loads(content)
        except JSONDecodeError:
            self.fail('The response content could not be loaded.')
        self.assertEqual(json_content.get('reason'), reason)
        self.assertEqual(json_content.get('queryset_count'), queryset_count)


class AdminViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up user accounts with different access privileges."""
        super().setUpClass()
        cls.super_user = User.objects.create_superuser(
            username='super_user',
            password='secret',
            email='super_user@example.com',
            is_superuser=True
        )
        cls.staff_user = User.objects.create_user(
            username='staff_user',
            password='secret',
            email='staff_user@example.com',
            is_staff=True
        )
        cls.regular_user = User.objects.create_user(
            username='regular_user',
            password='secret',
            email='regular_user@example.com'
        )

    def test_index_view(self):
        """
        Test the admin view through the statistics
        index view, which is restricted to admins.
        """
        try:
            url = reverse('statistics:index')
        except NoReverseMatch as e:
            self.fail(e)
        for allowed_user in [self.super_user, self.staff_user]:
            self.client.force_login(allowed_user)
            response = self.client.get(url, follow=True)
            self.assertEqual(response.status_code, HTTPStatus.OK)
        self.client.force_login(self.regular_user)
        response = self.client.get(url, follow=False)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.client.logout()
        response = self.client.get(url, follow=False)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)


class TemplateViewsIntegrationTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up a superuser account to access the statistics template views."""
        super().setUpClass()
        cls.super_user = User.objects.create_superuser(
            username='super_user',
            password='secret',
            email='super_user@example.com',
            is_superuser=True
        )

    def test_solutions_histogram_template_view(self):
        """
        Validate, that the solutions histogram template view
        is integrated and renders correctly.
        """
        try:
            url = reverse('statistics:submissions_histogram')
        except NoReverseMatch as e:
            self.fail(e)
        self.client.force_login(self.super_user)
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_attempts_histogram_template_view(self):
        """
        Validate, that the attempts histogram template view
        is integrated and renders correctly.
        """
        try:
            url = reverse('statistics:attempts_histogram')
        except NoReverseMatch as e:
            self.fail(e)
        self.client.force_login(self.super_user)
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)


class SubmissionsHistogramJsonViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up solutions to validate the histogram."""
        super().setUpClass()
        cls.super_user = User.objects.create_superuser(
            username='super_user',
            password='secret',
            email='super_user@example.com',
            is_superuser=True
        )
        cls.category = Category.objects.create(id=1337, name="Test Category")
        cls.task = Task.objects.create(
            pubdate='2000-01-01 00:00Z',
            category_id=1337,
            title='Fibonacci',
            slug='task'
        )

        submission_date = make_aware(datetime.strptime('01-01-1970', '%d-%m-%Y'))

        cls.first_solution = Solution.objects.create(
            author=cls.super_user, task=cls.task, passed=True
        )
        cls.first_solution.submission_date = submission_date
        cls.first_solution.save()
        cls.second_solution = Solution.objects.create(
            author=cls.super_user, task=cls.task, passed=True
        )
        cls.second_solution.submission_date = submission_date
        cls.second_solution.save()

    def setUp(self):
        """Prepare the submissions histogram api url."""
        super().setUp()
        try:
            self.url = reverse('statistics:submissions_histogram_api')
        except NoReverseMatch as error:
            self.fail(error)

    def test_bad_request(self):
        """Test the view's response to a bad request."""
        self.client.force_login(self.super_user)
        response = self.client.get(self.url, {'from_timestamp': '😈'}, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_queryset_limit_reached(self):
        """Test the view's response to exceeding the queryset limit."""
        self.client.force_login(self.super_user)
        response = self.client.get(self.url, {'queryset_limit': 0}, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_histogram(self):
        """
        Validate that the histogram is formed
        correctly when all parameters are supplied.
        """
        self.client.force_login(self.super_user)
        response = self.client.get(self.url, {
            'from_timestamp': '1970-01-01',
            'to_timestamp': '1970-01-01',
            'granularity': 'day',
            'passed': True,
            'category_id': self.category.id
        })
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response.content)
        try:
            data = json.loads(response.content)
        except JSONDecodeError:
            self.fail('The returned data should be valid JSON')
        histogram = data.get('histogram')
        self.assertIsNotNone(histogram)
        # The histogram should contain one bucket with both solutions
        self.assertEqual(len(histogram), 1)
        self.assertEqual(histogram[0]['count'], 2)


class AttemptsHistogramJsonViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up attempts to validate the histogram."""
        super().setUpClass()
        cls.super_user = User.objects.create_superuser(
            username='super_user',
            password='secret',
            email='super_user@example.com',
            is_superuser=True
        )
        cls.regular_user = User.objects.create_user(
            username='regular_user',
            password='secret',
            email='regular_user@example.com'
        )
        cls.category = Category.objects.create(id=1337, name="Test Category")
        cls.task = Task.objects.create(
            pubdate='2000-01-01 00:00Z',
            category_id=1337,
            title='Fibonacci',
            slug='task'
        )

        # Create attempts for the super user, where the first
        # passed solution should have the scoped_id 4
        for passed in [False, False, False, True, False, True]:
            Solution.objects.create(author=cls.super_user, task=cls.task, passed=passed)

        # Create attempts for the regular user, where the first
        # passed solution was the first try already, and then
        # the user fiddled around and submitted some more solutions
        for passed in [True, False, False, True]:
            Solution.objects.create(author=cls.regular_user, task=cls.task, passed=passed)

    def setUp(self):
        """Prepare the attempts histogram api url."""
        super().setUp()
        try:
            self.url = reverse('statistics:attempts_histogram_api')
        except NoReverseMatch as error:
            self.fail(error)

    def test_bad_json_request(self):
        """Test the view's response to a malformed json request."""
        self.client.force_login(self.super_user)
        response = self.client.get(self.url, {'task_id': '😈'}, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_queryset_limit_reached(self):
        """Test the views' response to crossing the queryset limit."""
        self.client.force_login(self.super_user)
        response = self.client.get(self.url, {
            'task_id': self.task.id, 'queryset_limit': 0
        }, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_no_task_id_parameter(self):
        """
        Test the view's response to a request
        without the mandatory task_id parameter.
        """
        self.client.force_login(self.super_user)
        response = self.client.get(self.url, {}, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_histogram(self):
        """
        Validate that the histogram is formed
        correctly when all parameters are supplied.
        """
        self.client.force_login(self.super_user)
        response = self.client.get(self.url, {
            'task_id': self.task.id
        })
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response.content)
        try:
            data = json.loads(response.content)
        except JSONDecodeError:
            self.fail('The returned data should be valid JSON')
        histogram = data.get('histogram')
        self.assertIsNotNone(histogram)
        self.assertEqual(histogram, {'4': 1, '1': 1})
