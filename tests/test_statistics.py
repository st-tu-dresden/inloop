import json
from http import HTTPStatus
from json import JSONDecodeError

from django.contrib.auth import get_user_model
from django.core.exceptions import FieldError, ValidationError
from django.db.models import functions
from django.test import TestCase
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

from inloop.solutions.models import Solution
from inloop.statistics.validators import (ALLOWED_TRUNCATOR_IDENTIFIERS, ISOFORMAT_REGEX,
                                          get_optional_bool, get_optional_int,
                                          get_optional_timestamp,
                                          get_optional_truncator_identifier)
from inloop.statistics.views import bad_json_request, queryset_limit_reached
from inloop.tasks.models import Category, Task

User = get_user_model()


class IsoFormatTest(TestCase):
    def test_iso_format_regex(self):
        """Test the iso format regex against invalid and valid values."""
        for invalid_value in [
            '2020-01-01T00:00:00.9999',
            '1970.01.01T00:00:00.000Z',
            '1970.01.01T00:00:00.000Z',
            '2020-01-01T00:00:00_000Z',
            '2020-01-31T10:27:42.013Z This text should not be accepted',
            'This text should not be accepted 2020-01-31T10:27:42.013Z'
        ]:
            match = ISOFORMAT_REGEX.match(invalid_value)
            if match is not None:
                self.fail(
                    f'The iso format regex should not '
                    f'accept this value: {invalid_value}'
                )

        valid_value = '2020-01-01T00:00:00.000Z'
        match = ISOFORMAT_REGEX.match(valid_value)
        self.assertIsNotNone(
            match, f'The iso format regex should accept this value: {valid_value}'
        )


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
        """Validate, that all allowed truncator identifiers are supported by the backend."""
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
    def test_get_optional_timestamp(self):
        """Test the timestamp validator."""
        self.assertIsNone(get_optional_timestamp('inexistent_key', {}))
        with self.assertRaises(ValidationError):
            get_optional_timestamp('date', {
                'date': '2020-01-01T00:00:00.000Z invalid appended text'
            })
        valid_value = '2020-01-01T00:00:00.000Z'
        try:
            self.assertIsNotNone(get_optional_timestamp('date', {
                'date': valid_value
            }))
        except ValidationError:
            self.fail(f'get_optional_timestamp should accept {repr(valid_value)}')

    def test_get_optional_int(self):
        """Test the integer validator."""
        self.assertIsNone(get_optional_int('inexistent_key', {}))
        with self.assertRaises(ValidationError):
            get_optional_int('int', {
                'int': 'undefined'
            })
        for valid_value in ['1', 2, -1]:
            try:
                self.assertIsNotNone(get_optional_int('int', {
                    'int': valid_value
                }))
            except ValidationError:
                self.fail(f'get_optional_int should accept {repr(valid_value)}')

    def test_get_optional_bool(self):
        """Test the boolean validator."""
        self.assertIsNone(get_optional_bool('inexistent_key', {}))
        with self.assertRaises(ValidationError):
            get_optional_bool('bool', {
                'bool': 'undefined'
            })
        for valid_value in [True, False, 'True', 'False', 'true', 'false', 0, 1]:
            try:
                self.assertIsNotNone(get_optional_bool('bool', {
                    'bool': valid_value
                }))
            except ValidationError:
                self.fail(f'get_optional_bool should accept {repr(valid_value)}')

    def test_get_optional_truncator_identifier(self):
        """Test the optinoal truncator identifier validator."""
        self.assertIsNone(get_optional_truncator_identifier('inexistent_key', {}))
        with self.assertRaises(ValidationError):
            get_optional_truncator_identifier('truncator', {
                'truncator': 'lightyears'
            })
        for valid_value in ALLOWED_TRUNCATOR_IDENTIFIERS:
            try:
                self.assertIsNotNone(get_optional_truncator_identifier('truncator', {
                    'truncator': valid_value
                }))
            except ValidationError:
                self.fail(f'get_optional_truncator_identifier should accept {repr(valid_value)}')


class BadJsonRequestTest(TestCase):
    def test_bad_json_request(self):
        """Test the bad json request response."""
        reason = 'test_reason'
        response = bad_json_request(reason=reason)
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
        self.assertEqual(response.status_code, HTTPStatus.CONFLICT)
        content = response.content.decode()
        try:
            json_content = json.loads(content)
        except JSONDecodeError:
            self.fail('The response content could not be loaded.')
        self.assertEqual(json_content.get('reason'), reason)
        self.assertEqual(json_content.get('queryset_count'), queryset_count)


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

        cls.from_timestamp = '2020-01-01T00:00:00.000Z'
        cls.to_timestamp = '2021-01-01T00:00:00.000Z'

        cls.first_solution = Solution.objects.create(
            author=cls.super_user, task=cls.task, passed=True
        )
        cls.first_solution.submission_date = cls.from_timestamp
        cls.first_solution.save()
        cls.second_solution = Solution.objects.create(
            author=cls.super_user, task=cls.task, passed=True
        )
        cls.second_solution.submission_date = cls.to_timestamp
        cls.second_solution.save()

    def setUp(self):
        """Prepare the submissions histogram api url."""
        super().setUp()
        try:
            self.url = reverse('statistics:submissions_histogram_api')
        except NoReverseMatch as e:
            self.fail(e)

    def test_bad_json_request(self):
        """Test the view's response to a malformed json request."""
        self.client.force_login(self.super_user)
        response = self.client.get(self.url, {'from_timestamp': '😈'}, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_queryset_limit_reached(self):
        """Test the views' response to crossing the queryset limit."""
        self.client.force_login(self.super_user)
        response = self.client.get(self.url, {'queryset_limit': 0}, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.CONFLICT)

    def test_histogram(self):
        """
        Validate, that the histogram is formed
        correctly, when all parameters are supplied.
        """
        self.client.force_login(self.super_user)
        response = self.client.get(self.url, {
            'from_timestamp': self.from_timestamp,
            'to_timestamp': self.to_timestamp,
            'granularity': 'year',
            'passed': 'true',
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
        # The histogram should contain two buckets
        self.assertEquals(len(histogram), 2)


class AttemptsHistogramJsonViewTest(TestCase):
    # Test bad json request
    # Test histogram with all params
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
        except NoReverseMatch as e:
            self.fail(e)

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
        self.assertEqual(response.status_code, HTTPStatus.CONFLICT)

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
        Validate, that the histogram is formed
        correctly, when all parameters are supplied.
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
        self.assertEquals(histogram, {'4': 1, '1': 1})
