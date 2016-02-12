from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.conf import settings

from inloop.accounts.models import UserProfile, CourseOfStudy
from inloop.accounts.forms import UserForm
import inloop.tasks.views as task_views


class LoginSystemTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.password = '123456'
        self.course = CourseOfStudy.objects.create(name='test_course')
        self.data = {
            'username': 'john',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'password': 'abc123456',
            'password_repeat': 'abc123456',
            'course': self.course.id,
            'mat_num': '1234567'
        }
        self.user = UserProfile.objects.create_user(
            username='test_user',
            first_name='first_name',
            last_name='last_name',
            email='test@example.com',
            password=self.password,
            mat_num='0000000'
        )

    def test_successful_change_password(self):
        new_password = '12345678'
        cp_data = {
            'old_password': self.password,
            'password': new_password,
            'password_repeat': new_password
        }
        login_data = {
            'username': self.user.username,
            'password': new_password
        }
        self.client.login(username=self.user.username, password=self.password)
        resp = self.client.post('/accounts/change_password/', data=cp_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'accounts/message.html')
        self.assertContains(resp, 'Your password has been changed successfully!')
        self.client.logout()
        resp = self.client.post('/accounts/login/', data=login_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context['user'].is_authenticated())
        self.assertEqual(resp.context['user'].get_username(), self.user.username)

    def test_change_password_mismatch(self):
        new_password = '12345678'
        cp_data = {
            'old_password': self.password,
            'password': new_password,
            'password_repeat': 'Not the new password. :('
        }
        self.client.login(username=self.user.username, password=self.password)
        resp = self.client.post('/accounts/change_password/', data=cp_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'The two password fields didn&#39;t match.')

    def test_registration_notification_redirect(self):
        resp = self.client.post('/accounts/register/', data=self.data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'accounts/message.html')
        self.assertContains(resp, 'Your activation mail has been sent!')

    def test_activation_process_client(self):
        self.client.post('/accounts/register/', data=self.data, follow=True)
        user = UserProfile.objects.get(username='john')
        link = '/accounts/activate/' + user.activation_key
        resp = self.client.get(link, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'accounts/message.html')
        self.assertContains(resp, "Your account has been activated! You can now login.")

        # Try to login
        self.try_default_user_login()

    def test_activation_mail_send(self):
        uf = UserForm(self.data)
        self.assertTrue(uf.is_valid())
        user = uf.save(commit=False)
        user.set_password(uf.cleaned_data['password'])
        user.is_active = False
        user.save()
        user.send_activation_mail()
        link = "{0}accounts/activate/{1}".format(settings.DOMAIN, user.activation_key)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'INLOOP Activation')
        self.assertTrue(user.username in mail.outbox[0].body)
        self.assertTrue(link in mail.outbox[0].body)

    def test_registration_form_errors(self):
        # Provoke username and email collision
        collision_data = {
            'username': 'john',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'password': '123',          # Too short
            'password_repeat': '123',
            'mat_num': '12345678'       # Too long
        }
        self.client.post('/accounts/register/', data=self.data, follow=True)
        resp = self.client.post('/accounts/register/', data=collision_data, follow=True)
        self.assertTemplateUsed(resp, 'registration/register.html')
        self.assertContains(resp, 'User with this Username already exists.')
        self.assertContains(resp, 'The password must have at least 8 characters!')
        self.assertContains(resp, 'This field is required.')  # From missing course choice
        self.assertContains(resp, 'The matriculation number does not have 7 digits!')

    def test_registration_form_password_mismatch(self):
        collision_data = self.data
        collision_data['password_repeat'] = '123'
        resp = self.client.post('/accounts/register/', data=collision_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'registration/register.html')
        self.assertContains(resp, 'The two password fields didn&#39;t match.')

    def test_registration_redirect_for_users(self):
        self.client.login(username=self.user.username, password=self.password)
        resp = self.client.get('/accounts/register/', follow=True)
        self.assertTemplateUsed(resp, 'tasks/index.html')
        self.assertRedirects(resp, '/')

    def test_login_redirect_for_users(self):
        self.client.login(username=self.user.username, password=self.password)
        resp = self.client.get('/accounts/login/', follow=True)
        self.assertTemplateUsed(resp, 'tasks/index.html')
        self.assertRedirects(resp, '/')

    def test_registration_password_consistency(self):
        uf = UserForm(self.data)
        self.assertTrue(uf.is_valid())
        user = uf.save(commit=False)
        user.set_password(uf.cleaned_data['password'])
        user.is_active = True  # Skip activation mail
        user.save()

        # Test login with fresh user
        self.try_default_user_login()

    def try_default_user_login(self):
        resp = self.client.post('/accounts/login/', data=self.data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'tasks/index.html')
        self.assertTrue(resp.context['user'].is_authenticated())
        self.assertEqual(resp.context['user'].get_username(), self.data['username'])
        self.assertContains(resp, '>john<')

    def test_anonymous_login_form(self):
        request = self.factory.get('/')
        request.user = AnonymousUser()
        resp = task_views.index(request)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'registration/login.html')
        self.assertContains(resp, '>Login<')

    def test_successful_system_login(self):
        credentials = {
            'username': self.user.username,
            'password': self.password
        }
        resp = self.client.post('/accounts/login/', data=credentials, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'tasks/index.html')
        self.assertTrue(resp.context['user'].is_authenticated())
        self.assertEqual(resp.context['user'].get_username(), self.user.username)
        self.assertContains(resp, '>test_user<')

    def test_unsuccessful_system_login(self):
        credentials = {
            'username': self.user.username,
            'password': 'invalid'
        }
        resp = self.client.post('/accounts/login/', data=credentials, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'registration/login.html')
        self.assertFalse(resp.context['user'].is_authenticated())
        self.assertContains(resp, '>Login<')
        self.assertNotContains(resp, '>test_user<')
