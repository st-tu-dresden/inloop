import re

from django.contrib.sites.models import Site
from django.core import mail
from django.db.models import ObjectDoesNotExist
from django.test import TestCase
from django.urls import reverse

from constance.test import override_config

from inloop.accounts.forms import SignupForm, StudentDetailsForm
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


class ProfileViewTest(SimpleAccountsData, TestCase):
    URL = reverse("accounts:profile")

    def test_form_submit(self):
        with self.assertRaises(ObjectDoesNotExist):
            StudentDetails.objects.get(user=self.bob)
        self.assertTrue(self.client.login(username="bob", password="secret"))
        response = self.client.post(self.URL, data={
            "matnum": "1234567",
            "first_name": "Bob",
            "last_name": "Example",
            "course": "1",
        }, follow=True)
        self.assertContains(response, "Your profile has been updated successfully.")
        details = StudentDetails.objects.get(user=self.bob)
        self.assertEqual(details.matnum, "1234567")
        self.assertEqual(details.user, self.bob)
        self.assertEqual(details.user.first_name, "Bob")
        self.assertEqual(details.user.last_name, "Example")


@override_config(
    SIGNUP_ALLOWED=True,
    EMAIL_PATTERN=r"@example\.org\Z",
    EMAIL_ERROR_MESSAGE="This address does not end in `@example.org`."
)
class SignupFormTest(SimpleAccountsData, TestCase):
    def test_submit_invalid_email(self):
        form = SignupForm(data={"email": "bob@example.com"})
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertEqual(form.errors["email"], [
            "<p>This address does not end in <code>@example.org</code>.</p>"
        ])

    def test_case_insensitive_email_already_in_use(self):
        form = SignupForm(data={"email": "Bob@example.org"})
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertEqual(len(form.errors["email"]), 1)
        self.assertIn("This email address is already in use.", form.errors["email"][0])

    def test_case_insensitive_user_already_exists(self):
        form = SignupForm(data={"username": "Bob"})
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)
        self.assertEqual(form.errors["username"], ["A user with that username already exists."])


class SignupViewTests(SimpleAccountsData, TestCase):
    URL = reverse("accounts:signup")

    def test_reverse_url(self):
        self.assertEqual(self.URL, "/account/signup/")

    @override_config(SIGNUP_ALLOWED=True)
    def test_signup_anonymous_users_only(self):
        response = self.client.get(self.URL)
        self.assertContains(response, "Sign up")

        self.assertTrue(self.client.login(username="bob", password="secret"))
        response = self.client.get(self.URL)
        self.assertRedirects(
            response, "/", msg_prefix="Signup view should redirect authenticated users"
        )

    def test_signup_disallowed(self):
        response1 = self.client.get(self.URL, follow=True)
        response2 = self.client.post(self.URL, follow=True)
        for response in [response1, response2]:
            self.assertContains(response, "Sorry, signing up is not allowed at the moment.")


class SignupWorkflowTest(TestCase):
    FORM_DATA = {
        "username": "bob",
        "email": "bob@example.org",
        "password1": "secret",
        "password2": "secret",
    }

    @classmethod
    def setUpTestData(cls):
        site = Site.objects.get_current()
        site.name = "INLOOP"
        site.domain = "example.com"
        site.save()

    @override_config(SIGNUP_ALLOWED=True)
    def test_signup_workflow(self):
        response = self.client.post(reverse("accounts:signup"), data=self.FORM_DATA, follow=True)
        self.assertContains(response, "Please check your mailbox.")

        self.assertFalse(self.client.login(username="bob", password="secret"),
                         "Login should fail before activation")

        subject, body = mail.outbox[0].subject, mail.outbox[0].body
        self.assertEqual(subject, "Activate your account on example.com")
        self.assertIn("Hello bob,", body)
        self.assertIn("The INLOOP team", body)

        link = re.search(r"https?://example\.com/account/activate/[-:\w]+/", body)
        self.assertIsNotNone(link, "The mail should contain an activation link")

        url = re.sub(r"https?://example\.com", "", link.group())
        response = self.client.get(url, follow=True)
        self.assertContains(response, "Your account has been activated.")

        response = self.client.get(url, follow=True)
        self.assertContains(response, "This activation link is not valid.",
                            msg_prefix="Activation link should be valid only once")

        self.assertTrue(self.client.login(username="bob", password="secret"),
                        "Login should succeed after activation")
