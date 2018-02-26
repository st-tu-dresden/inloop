import re

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from constance import config
from registration import validators
from registration.forms import RegistrationFormUniqueEmail

from inloop.accounts.models import StudentDetails
from inloop.common.templatetags.markdown import markdown


class SignupForm(RegistrationFormUniqueEmail):
    """
    A user-friendly sign up form with dynamically configurable help texts and validation.
    """

    # Have to redeclare the entire field from the super class in order
    # to add our own help text:
    email = forms.EmailField(
        help_text=lambda: markdown(config.EMAIL_HELP_TEXT),
        required=True,
        validators=[
            validators.validate_confusables_email,
        ]
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
