from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser

from inloop.accounts.models import UserProfile
from inloop.tasks.views import index


class LoginSystemTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.password = '123456'
        self.user = UserProfile.objects.create_user(
            username='test_user',
            first_name='first_name',
            last_name='last_name',
            email='test@example.com',
            password=self.password,
            mat_num='0000000'
        )

    def test_anonymous_login_form(self):
        request = self.factory.get('/')
        request.user = AnonymousUser()
        response = index(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '>Login<')

    def test_successful_system_login(self):
        credentials = {
            'username': self.user.username,
            'password': self.password
        }
        resp = self.client.post('/accounts/login/', data=credentials, follow=True)
        self.assertEqual(resp.status_code, 200)
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
        self.assertFalse(resp.context['user'].is_authenticated())
        self.assertContains(resp, '>Login<')
        self.assertNotContains(resp, '>test_user<')
