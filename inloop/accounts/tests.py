from django.test import TestCase
from django.core import mail
from django.conf import settings

from inloop.accounts.models import UserProfile, CourseOfStudy
from inloop.accounts.forms import UserForm


class RegistrationTests(TestCase):
    def setUp(self):
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
            course=self.course,
            mat_num='0000000'
        )

    def assert_response_template_contains(self, resp, template, content):
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, template)
        self.assertContains(resp, content)

    def try_default_user_login(self):
        resp = self.client.post('/accounts/login/', data=self.data, follow=True)
        self.assert_response_template_contains(
            resp=resp,
            template='tasks/index.html',
            content='>john<'
        )
        self.assertTrue(resp.context['user'].is_authenticated())
        self.assertEqual(resp.context['user'].get_username(), self.data['username'])

    def test_registration_password_consistency(self):
        uf = UserForm(self.data)
        self.assertTrue(uf.is_valid())
        user = uf.save(commit=False)
        user.set_password(uf.cleaned_data['password'])
        user.is_active = True  # Skip activation mail
        user.save()

        # Test login with fresh user
        self.try_default_user_login()

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
        self.assert_response_template_contains(
            resp=resp,
            template='registration/register.html',
            content='The two password fields didn&#39;t match.'
        )

    def test_registration_redirect_for_users(self):
        self.client.login(username=self.user.username, password=self.password)
        resp = self.client.get('/accounts/register/', follow=True)
        self.assertTemplateUsed(resp, 'tasks/index.html')
        self.assertRedirects(resp, '/')

    def test_registration_notification_redirect(self):
        resp = self.client.post('/accounts/register/', data=self.data, follow=True)
        self.assert_response_template_contains(
            resp=resp,
            template='accounts/message.html',
            content='Your activation mail has been sent.'
        )

    def test_activation_process_client(self):
        self.client.post('/accounts/register/', data=self.data, follow=True)
        user = UserProfile.objects.get(username='john')
        link = '/accounts/activate/' + user.activation_key
        resp = self.client.get(link, follow=True)
        self.assert_response_template_contains(
            resp=resp,
            template='accounts/message.html',
            content='Your account has been activated! You can now login.'
        )

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
        self.assertEqual(mail.outbox[0].subject, 'INLOOP account activation')
        self.assertTrue(user.username in mail.outbox[0].body)
        self.assertTrue(link in mail.outbox[0].body)


class ProfileTests(TestCase):
    def setUp(self):
        self.password = '123456'
        self.new_password = '12345678'
        self.course1 = CourseOfStudy.objects.create(name='test_course')
        self.course2 = CourseOfStudy.objects.create(name='another_test_course')
        self.profile_data = {
            'mat_num': 1111111,
            'course': self.course1.id
        }
        self.user = UserProfile.objects.create_user(
            username='test_user',
            first_name='first_name',
            last_name='last_name',
            email='test@example.com',
            password=self.password,
            course=self.course1,
            mat_num='0000000'
        )

    def assert_response_template_contains(self, resp, template, content):
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, template)
        self.assertContains(resp, content)

    def test_successful_course_change(self):
        prof_data = self.profile_data.copy()
        prof_data.update({'course': self.course2.id})

        self.client.login(username=self.user.username, password=self.password)
        resp = self.client.post('/accounts/profile/', data=prof_data, follow=True)
        self.assert_response_template_contains(
            resp=resp,
            template='accounts/message.html',
            content='Your profile information has successfully been changed.'
        )
        self.assertEqual(resp.context['user'].course.id, prof_data['course'])

    def test_invalid_course_change(self):
        prof_data = self.profile_data.copy()
        prof_data.update({'course': 1337})  # Invalid course id

        self.client.login(username=self.user.username, password=self.password)
        resp = self.client.post('/accounts/profile/', data=prof_data, follow=True)
        self.assert_response_template_contains(
            resp=resp,
            template='accounts/profile.html',
            content='Select a valid choice. That choice is not one of the available choices.'
        )
        self.assertEqual(resp.context['user'].course.id, self.profile_data['course'])

    def test_successful_user_profile_change_mat_num(self):
        self.client.login(username=self.user.username, password=self.password)
        resp = self.client.post('/accounts/profile/', data=self.profile_data, follow=True)
        self.assert_response_template_contains(
            resp=resp,
            template='accounts/message.html',
            content='Your profile information has successfully been changed.'
        )
        self.assertEqual(resp.context['user'].mat_num, self.profile_data['mat_num'])

    def test_user_profile_long_mat_num(self):
        prof_data = self.profile_data.copy()
        prof_data.update({'mat_num': 11111111})
        self.client.login(username=self.user.username, password=self.password)
        resp = self.client.post('/accounts/profile/', data=prof_data, follow=True)
        self.assert_response_template_contains(
            resp=resp,
            template='accounts/profile.html',
            content='The matriculation number does not have 7 digits!'
        )

    def test_user_profile_short_mat_num(self):
        prof_data = self.profile_data.copy()
        prof_data.update({'mat_num': 111111})
        self.client.login(username=self.user.username, password=self.password)
        resp = self.client.post('/accounts/profile/', data=prof_data, follow=True)
        self.assert_response_template_contains(
            resp=resp,
            template='accounts/profile.html',
            content='The matriculation number does not have 7 digits!'
        )

    def test_user_profile_alphanumeric_mat_num(self):
        prof_data = self.profile_data.copy()
        prof_data.update({'mat_num': '11111a'})
        self.client.login(username=self.user.username, password=self.password)
        resp = self.client.post('/accounts/profile/', data=prof_data, follow=True)
        self.assert_response_template_contains(
            resp=resp,
            template='accounts/profile.html',
            content='Enter a whole number.'
        )

    def test_successful_change_password(self):
        cp_data = {
            'old_password': self.password,
            'new_password1': self.new_password,
            'new_password2': self.new_password
        }
        login_data = {
            'username': self.user.username,
            'password': self.new_password
        }
        self.client.login(username=self.user.username, password=self.password)
        resp = self.client.post('/accounts/password_change/', data=cp_data, follow=True)
        self.assert_response_template_contains(
            resp=resp,
            template='registration/password_change_done.html',
            content='Your password has been changed successfully.'
        )
        self.client.logout()
        resp = self.client.post('/accounts/login/', data=login_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context['user'].is_authenticated())
        self.assertEqual(resp.context['user'].get_username(), self.user.username)

    def test_change_password_mismatch(self):
        cp_data = {
            'old_password': self.password,
            'new_password1': self.new_password,
            'new_password2': 'Not the new password. :('
        }
        self.client.login(username=self.user.username, password=self.password)
        resp = self.client.post('/accounts/password_change/', data=cp_data, follow=True)
        self.assert_response_template_contains(
            resp=resp,
            template='registration/password_change_form.html',
            content='The two password fields didn&#39;t match.'
        )

    def change_password_missing_field_assertions(self, cp_data):
        self.client.login(username=self.user.username, password=self.password)
        resp = self.client.post('/accounts/password_change/', data=cp_data, follow=True)
        self.assert_response_template_contains(
            resp=resp,
            template='registration/password_change_form.html',
            content='This field is required.'
        )

    def test_change_password_missing_old_password(self):
        cp_data = {
            'password': self.new_password,
            'password_repeat': self.new_password
        }
        self.change_password_missing_field_assertions(cp_data)

    def test_change_password_missing_password(self):
        cp_data = {
            'old_password': self.password,
            'new_password2': self.new_password
        }
        self.change_password_missing_field_assertions(cp_data)

    def test_change_password_missing_password_repeat(self):
        cp_data = {
            'old_password': self.password,
            'new_password1': self.new_password
        }
        self.change_password_missing_field_assertions(cp_data)


class LoginSystemTests(TestCase):
    def setUp(self):
        self.password = '123456'
        self.course = CourseOfStudy.objects.create(name='test_course')
        self.user = UserProfile.objects.create_user(
            username='test_user',
            first_name='first_name',
            last_name='last_name',
            email='test@example.com',
            password=self.password,
            course=self.course,
            mat_num='0000000'
        )

    def assert_response_template_contains(self, resp, template, content):
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, template)
        self.assertContains(resp, content)

    def test_login_redirect_for_users(self):
        self.client.login(username=self.user.username, password=self.password)
        resp = self.client.get('/accounts/login/', follow=True)
        self.assertTemplateUsed(resp, 'tasks/index.html')
        self.assertRedirects(resp, '/')

    def test_anonymous_login_form(self):
        resp = self.client.get('/')
        self.assert_response_template_contains(
            resp=resp,
            template='registration/login.html',
            content='>Login<'
        )

    def test_successful_system_login(self):
        credentials = {
            'username': self.user.username,
            'password': self.password
        }
        resp = self.client.post('/accounts/login/', data=credentials, follow=True)
        self.assert_response_template_contains(
            resp=resp,
            template='tasks/index.html',
            content='>test_user<'
        )
        self.assertTrue(resp.context['user'].is_authenticated())
        self.assertEqual(resp.context['user'].get_username(), self.user.username)

    def test_unsuccessful_system_login(self):
        credentials = {
            'username': self.user.username,
            'password': 'invalid'
        }
        resp = self.client.post('/accounts/login/', data=credentials, follow=True)
        self.assert_response_template_contains(
            resp=resp,
            template='registration/login.html',
            content='>Login<',
        )
        self.assertNotContains(resp, '>test_user<')
        self.assertFalse(resp.context['user'].is_authenticated())
