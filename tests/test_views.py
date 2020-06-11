from django.contrib.auth import SESSION_KEY
from django.test import TestCase
from django.urls import reverse

from tests.accounts.mixins import SimpleAccountsData


class ProtectedLogoutTest(SimpleAccountsData, TestCase):
    def test_method_not_allowed(self):
        for url in [reverse('logout'), reverse('admin:logout')]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 405)

    def test_logout(self):
        self.assertTrue(self.client.login(username='bob', password='secret'))
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('home'))
        self.assertNotIn(SESSION_KEY, self.client.session)
