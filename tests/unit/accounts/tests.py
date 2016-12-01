from unittest import skip

from django.contrib.sites.models import Site
from django.core import mail
from django.test import TestCase


class RegistrationTests(TestCase):
    FORM_DATA = {
        "username": "bob",
        "email": "bob@example.org",
        "password1": "Passw0rd!",
        "password2": "Passw0rd!",
    }

    @skip
    def test_registration(self):
        """Test if a complete activation email is sent after a successful registration."""
        self.assertEqual(Site.objects.get_current().domain, "example.com")
        response = self.client.post("/accounts/register/", data=self.FORM_DATA, follow=True)
        activation_mail = mail.outbox[0]
        link_pattern = r"\bhttp://example\.com/accounts/activate/[0-9a-zA-Z]{40}\b"
        self.assertContains(response, "Your activation mail has been sent.")
        self.assertEqual(activation_mail.subject, "Activate your account on example.com")
        self.assertIn("Hello John,", activation_mail.body)
        self.assertRegex(activation_mail.body, link_pattern)
