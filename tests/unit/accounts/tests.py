from unittest import skip

from django.contrib.sites.models import Site
from django.core import mail
from django.test import TestCase

from inloop.accounts.forms import StudentDetailsForm
from inloop.accounts.models import Course, StudentDetails

from tests.unit.accounts.mixins import SimpleAccountsData


class AccountModelsTest(SimpleAccountsData, TestCase):
    def test_default_callable(self):
        details = StudentDetails.objects.create(user=self.bob)
        self.assertEqual(str(details), "bob")
        self.assertEqual(str(details.course), "Other")
        self.assertTrue(Course.objects.get(name="Other"))


class StudentDetailsFormTest(TestCase):
    def test_matnum_validation(self):
        form1 = StudentDetailsForm(data={"matnum": "invalid"})
        form2 = StudentDetailsForm(data={"matnum": ""})
        form3 = StudentDetailsForm(data={"matnum": "1234567"})
        self.assertIn("matnum", form1.errors)
        self.assertNotIn("matnum", form2.errors)
        self.assertNotIn("matnum", form3.errors)


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
