from django.test import TestCase
from accounts.models import UserProfile


class LoginSystemTests(TestCase):
    def setUp(self):
        self.password = '123456'
        UserProfile.objects.create_user(username='test_user',
                                        first_name='first_name',
                                        last_name='last_name',
                                        email='test@example.com',
                                        password=self.password,
                                        mat_num='0000000')

    def test_anonymous_redirect(self):
        # redirect to login page for anonymous users
        resp = self.client.get('/', follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('csrf_token' in resp.context)
        self.assertRedirects(resp, '/accounts/login/?next=/')

    def test_successful_system_login(self):
        user = UserProfile.objects.get(username='test_user')
        self.client.login(username=user.username, password=self.password)
        resp = self.client.get('/', follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context['user'].is_authenticated())
        self.assertEqual(resp.context['user'].get_username(), user.username)

    def test_unsuccessful_system_login(self):
        user = UserProfile.objects.get(username='test_user')
        self.client.login(username=user.username, password='wrong password!')
        resp = self.client.get('/', follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertRedirects(resp, '/accounts/login/?next=/')
        self.assertFalse(resp.context['user'].is_authenticated())
