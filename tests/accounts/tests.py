import re
from datetime import timedelta
from io import StringIO
from unittest import mock

from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site
from django.core import mail
from django.core.management import call_command
from django.db.models import ObjectDoesNotExist
from django.test import TestCase, override_settings
from django.urls import reverse

from constance.test import override_config

from inloop.accounts.forms import SignupForm, StudentDetailsForm
from inloop.accounts.models import (Course, StudentDetails,
                                    prune_invalid_users, user_profile_complete)
from inloop.accounts.tasks import autoprune_invalid_users

from tests.accounts.mixins import SimpleAccountsData


class AccountModelsTest(TestCase):
    def setUp(self):
        """Create a fresh user object for each test, so we can modify it."""
        super().setUp()
        self.sarah = User.objects.create_user(
            username='sarah',
            email='sarah@example.org',
            password='secret'
        )

    def test_course_default(self):
        details = StudentDetails.objects.create(user=self.sarah)
        self.assertEqual(str(details), 'sarah')
        self.assertEqual(str(details.course), 'Other')
        self.assertTrue(Course.objects.get(name='Other'))

    def test_profile_complete1(self):
        """Profile is not complete when related StudentDetails object is missing."""
        with self.assertRaises(User.studentdetails.RelatedObjectDoesNotExist):
            self.sarah.studentdetails
        self.assertFalse(user_profile_complete(self.sarah))

    def test_profile_complete2(self):
        """Profile is not complete when matnum, first_name or last_name fields are empty."""
        StudentDetails.objects.create(user=self.sarah)
        self.assertTrue(self.sarah.studentdetails)
        self.assertFalse(user_profile_complete(self.sarah))

    def test_profile_complete3(self):
        """Profile is complete when matnum, first_name and last_name are not empty."""
        StudentDetails.objects.create(user=self.sarah, matnum='1234567')
        self.assertTrue(self.sarah.studentdetails)
        self.sarah.first_name = 'Sarah'
        self.sarah.last_name = 'Connor'
        self.sarah.save()
        self.assertTrue(user_profile_complete(self.sarah))

    @mock.patch('inloop.accounts.models.messages')
    def test_profile_complete_signal1(self, mocked_messages):
        """After logging in, no message is displayed for a complete profile."""
        StudentDetails.objects.create(user=self.sarah, matnum='1234567')
        self.sarah.first_name = 'Sarah'
        self.sarah.last_name = 'Connor'
        self.sarah.save()
        self.client.login(username='sarah', password='secret')
        self.assertFalse(mocked_messages.warning.called)

    @mock.patch('inloop.accounts.models.messages')
    def test_profile_complete_signal2(self, mocked_messages):
        """After logging in, a message is displayed for an incomplete profile."""
        self.client.login(username='sarah', password='secret')
        self.assertTrue(mocked_messages.warning.called)


@override_settings(ACCOUNT_ACTIVATION_DAYS=1)
class PruneInvalidUsersTest(TestCase):
    TIMEDELTA = timedelta(days=1, seconds=1)

    def setUp(self):
        super().setUp()
        self.bob = User.objects.create_user('bob', 'bob@example.com', 'secret')

    def test_active_accounts_are_not_deleted(self):
        # TEST 1: active with date_joined older than deadline NOT deleted
        self.bob.date_joined -= self.TIMEDELTA
        self.bob.save()
        num_deleted = prune_invalid_users()
        self.assertEqual(num_deleted, 0)
        self.assertTrue(User.objects.filter(username='bob').exists())

    def test_inactive_but_used_accounts_are_not_deleted(self):
        # TEST 2: inactive but already logged in with date_joined older than deadline NOT deleted
        self.bob.date_joined -= self.TIMEDELTA
        self.bob.last_login = self.bob.date_joined
        self.bob.is_active = False
        self.bob.save()
        num_deleted = prune_invalid_users()
        self.assertEqual(num_deleted, 0)
        self.assertTrue(User.objects.filter(username='bob').exists())

    def test_activatable_accounts_are_not_deleted(self):
        # TEST 3: inactive, never logged in, before deadline NOT deleted
        self.bob.is_active = False
        self.bob.save()
        num_deleted = prune_invalid_users()
        self.assertEqual(num_deleted, 0)
        self.assertTrue(User.objects.filter(username='bob').exists())

    def test_inactive_unused_accounts_are_deleted(self):
        # TEST 4: inactive, never logged in, older than deadline deleted
        self.bob.date_joined -= self.TIMEDELTA
        self.bob.is_active = False
        self.bob.save()
        num_deleted = prune_invalid_users()
        self.assertEqual(num_deleted, 1)
        self.assertFalse(User.objects.filter(username='bob').exists())

    def test_integration_with_management_command(self):
        self.bob.date_joined -= self.TIMEDELTA
        self.bob.is_active = False
        self.bob.save()
        stdout = StringIO()
        call_command('prune_invalid_users', stdout=stdout)
        self.assertIn('Pruned 1 invalid account(s)', stdout.getvalue())
        self.assertFalse(User.objects.filter(username='bob').exists())

    def test_integration_with_queue(self):
        self.bob.date_joined -= self.TIMEDELTA
        self.bob.is_active = False
        self.bob.save()
        with self.assertLogs() as capture_logs:
            autoprune_invalid_users.call_local()
        self.assertIn('Pruned 1 invalid account(s)', capture_logs.output[0])
        self.assertFalse(User.objects.filter(username='bob').exists())


class AssignUsersTest(TestCase):
    def setUp(self):
        super().setUp()
        self.bob = User.objects.create_user('bob', 'bob@example.com', 'secret')
        self.alice = User.objects.create_user('alice', 'alice@example.com', 'secret')
        self.frank = User.objects.create_user('frank', 'frank@example.com', 'secret')

    def test_initial_assign_to_group(self):
        stdout = StringIO()
        call_command('assign_groups', 'Group1', 'Group2', stdout=stdout)
        self.assertEqual(1, self.bob.groups.count())
        self.assertIn(self.bob.groups.first().name, ['Group1', 'Group2'])
        self.assertEqual(1, self.alice.groups.count())
        self.assertIn(self.alice.groups.first().name, ['Group1', 'Group2'])
        self.assertEqual(1, self.frank.groups.count())
        self.assertIn(self.frank.groups.first().name, ['Group1', 'Group2'])

    def test_existing_assign_to_group(self):
        self.bob.groups.add(Group.objects.create(name='Already assigned group'))
        stdout = StringIO()
        call_command('assign_groups', 'Group1', 'Group2', stdout=stdout)
        self.assertEqual(1, self.bob.groups.count())
        self.assertEqual(self.bob.groups.first().name, 'Already assigned group')
        self.assertEqual(1, self.alice.groups.count())
        self.assertIn(self.alice.groups.first().name, ['Group1', 'Group2'])
        self.assertEqual(1, self.frank.groups.count())
        self.assertIn(self.frank.groups.first().name, ['Group1', 'Group2'])


class StudentDetailsFormTest(TestCase):
    def test_matnum_validation(self):
        form1 = StudentDetailsForm(data={'matnum': 'invalid'})
        form2 = StudentDetailsForm(data={'matnum': ''})
        form3 = StudentDetailsForm(data={'matnum': '1234567'})
        self.assertIn('matnum', form1.errors)
        self.assertNotIn('matnum', form2.errors)
        self.assertNotIn('matnum', form3.errors)


class ProfileViewTest(SimpleAccountsData, TestCase):
    URL = reverse('accounts:profile')

    def test_form_submit(self):
        with self.assertRaises(ObjectDoesNotExist):
            StudentDetails.objects.get(user=self.bob)
        self.assertTrue(self.client.login(username='bob', password='secret'))
        response = self.client.post(self.URL, data={
            'matnum': '1234567',
            'first_name': 'Bob',
            'last_name': 'Example',
            'course': '1',
        }, follow=True)
        self.assertContains(response, 'Your profile has been updated successfully.')
        details = StudentDetails.objects.get(user=self.bob)
        self.assertEqual(details.matnum, '1234567')
        self.assertEqual(details.user, self.bob)
        self.assertEqual(details.user.first_name, 'Bob')
        self.assertEqual(details.user.last_name, 'Example')


@override_config(
    SIGNUP_ALLOWED=True,
    EMAIL_PATTERN=r'@example\.org\Z',
    EMAIL_ERROR_MESSAGE='This address does not end in `@example.org`.'
)
class SignupFormTest(SimpleAccountsData, TestCase):
    def test_submit_invalid_email(self):
        form = SignupForm(data={'email': 'bob@example.com'})
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertEqual(form.errors['email'], [
            '<p>This address does not end in <code>@example.org</code>.</p>'
        ])

    def test_case_insensitive_email_already_in_use(self):
        form = SignupForm(data={'email': 'Bob@example.org'})
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertEqual(len(form.errors['email']), 1)
        self.assertIn('This email address is already in use.', form.errors['email'][0])

    def test_case_insensitive_user_already_exists(self):
        form = SignupForm(data={'username': 'Bob'})
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertEqual(form.errors['username'], ['A user with that username already exists.'])


class SignupViewTests(SimpleAccountsData, TestCase):
    URL = reverse('accounts:signup')

    def test_reverse_url(self):
        self.assertEqual(self.URL, '/account/signup/')

    @override_config(SIGNUP_ALLOWED=True)
    def test_signup_anonymous_users_only(self):
        response = self.client.get(self.URL)
        self.assertContains(response, 'Sign up')

        self.assertTrue(self.client.login(username='bob', password='secret'))
        response = self.client.get(self.URL)
        self.assertRedirects(
            response, '/', msg_prefix='Signup view should redirect authenticated users'
        )

    def test_signup_disallowed(self):
        response1 = self.client.get(self.URL, follow=True)
        response2 = self.client.post(self.URL, follow=True)
        for response in [response1, response2]:
            self.assertContains(response, 'Sorry, signing up is not allowed at the moment.')


class SignupWorkflowTest(TestCase):
    FORM_DATA = {
        'username': 'bob',
        'email': 'bob@example.org',
        'password1': 'secret',
        'password2': 'secret',
        'privacy_consent': 'true',
    }

    @classmethod
    def setUpTestData(cls):
        site = Site.objects.get_current()
        site.name = 'INLOOP'
        site.domain = 'example.com'
        site.save()

    @override_config(SIGNUP_ALLOWED=True)
    def test_signup_workflow(self):
        response = self.client.post(reverse('accounts:signup'), data=self.FORM_DATA, follow=True)
        self.assertContains(response, 'Please check your mailbox.')

        self.assertFalse(self.client.login(username='bob', password='secret'),
                         'Login should fail before activation')

        subject, body = mail.outbox[0].subject, mail.outbox[0].body
        self.assertEqual(subject, 'Activate your account on example.com')
        self.assertIn('Hello bob,', body)
        self.assertIn('The INLOOP team', body)

        link = re.search(r'https?://example\.com/account/activate/[-:\w]+/', body)
        self.assertIsNotNone(link, 'The mail should contain an activation link')

        url = re.sub(r'https?://example\.com', '', link.group())
        response = self.client.get(url, follow=True)
        self.assertContains(response, 'Your account has been activated.')

        response = self.client.get(url, follow=True)
        self.assertContains(response, 'This activation link is not valid.',
                            msg_prefix='Activation link should be valid only once')

        self.assertTrue(self.client.login(username='bob', password='secret'),
                        'Login should succeed after activation')


class PasswordRecoverWorkflowTest(SimpleAccountsData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        site = Site.objects.get_current()
        site.name = 'INLOOP'
        site.domain = 'example.com'
        site.save()

    def test_password_reset_link_present(self):
        response = self.client.get(reverse('login'), follow=True)
        self.assertContains(response, reverse('accounts:password_reset'))
        response = self.client.get(reverse('accounts:password_reset'))
        self.assertNotEqual(response.status_code, 404)

    def test_recovery(self):
        form_data = {'email': self.bob.email}
        response = self.client.post(
            reverse('accounts:password_reset'), data=form_data, follow=True
        )
        self.assertContains(
            response,
            "We've sent an email to you with further "
            'instructions to recover your account.'
        )

        subject, body = mail.outbox[0].subject, mail.outbox[0].body
        self.assertEqual(subject, 'Recover your password on example.com')
        self.assertIn('Hello bob,', body)
        self.assertIn('You (or someone pretending to be you) '
                      'has requested a password reset on example.com.', body)
        self.assertIn('The INLOOP team', body)

        link = re.search(
            r'https?://example\.com/account/password_reset_confirm/'
            r'(?P<uidb64>[0-9A-Za-z_\-]+)/'
            r'(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/',
            body
        )
        self.assertIsNotNone(link, 'The mail should contain a password reset link')

        url = re.sub(r'https?://example\.com', '', link.group())
        response = self.client.get(url, follow=True)
        self.assertContains(response, 'Set a new password')
        self.assertTrue(response.redirect_chain)
        current_location, status_code = response.redirect_chain[0]
        self.assertEqual(status_code, 302)

        form_data = {
            'new_password1': 'ji32k7au4a83',
            'new_password2': 'ji32k7au4a83'
        }
        response = self.client.post(current_location, data=form_data, follow=True)
        self.assertContains(response, 'Your new password has been saved.')

        self.assertTrue(self.client.login(username='bob', password='ji32k7au4a83'),
                        'Login should succeed after password reset')

        response = self.client.get(url, follow=True)
        self.assertContains(response, 'Sorry, this recovery link is invalid.')
