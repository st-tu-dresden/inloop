import re

from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError

from constance import config
from registration.forms import RegistrationFormUniqueEmail

from inloop.accounts.models import StudentDetails
from inloop.common.templatetags.markdown import markdown


class SignupForm(RegistrationFormUniqueEmail):
    """
    A user-friendly sign up form with dynamically configurable help texts and validation.
    """

    email = forms.EmailField(
        label="Email",
        help_text=lambda: markdown(config.EMAIL_HELP_TEXT)
    )

    # Workaround for Django ticket #26097 until 1.11 is released:
    # We need to override this field to include the help text of the
    # configured AUTH_PASSWORD_VALIDATORS.
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        strip=False,
        help_text=password_validation.password_validators_help_text_html()
    )

    def clean_email(self):
        """Perform additional email validation if configured in the admin interface."""
        pattern = config.EMAIL_PATTERN
        if pattern:
            # The pattern is always validated in the admin interface by testing if
            # re.compile() succeeds. If it fails to compile now, there must be some
            # serious error which we can't fix here and it's better to crash.
            regex = re.compile(pattern, re.VERBOSE)
            if not regex.search(self.cleaned_data["email"]):
                raise ValidationError(markdown(config.EMAIL_ERROR_MESSAGE))
        return super().clean_email()


class StudentDetailsForm(forms.ModelForm):
    class Meta:
        model = StudentDetails
        fields = ["matnum", "course"]


class UserChangeForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name"]
