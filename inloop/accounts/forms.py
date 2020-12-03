import re

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from constance import config
from django_registration import validators
from django_registration.forms import RegistrationFormUniqueEmail

from inloop.accounts.models import StudentDetails
from inloop.common.templatetags.markdown import markdown

User = get_user_model()


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
        ],
    )

    privacy_consent = forms.BooleanField(
        help_text='Yes, I accept the <a href="/about/privacy/">privacy statement</a>.',
        required=True,
    )

    def clean_email(self) -> str:
        """Perform additional email validation if configured in the admin interface."""
        pattern = config.EMAIL_PATTERN
        email = self.cleaned_data["email"]
        if pattern:
            # The pattern is always validated in the admin interface by testing if
            # re.compile() succeeds. If it fails to compile now, there must be some
            # serious error which we can't fix here and it's better to crash.
            regex = re.compile(pattern, re.VERBOSE)
            if not regex.search(email):
                raise ValidationError(markdown(config.EMAIL_ERROR_MESSAGE))
        return email

    def clean_username(self) -> str:
        """Ensure no duplicate user names exist, using case-insensitive comparison."""
        username = self.cleaned_data.get("username")
        if User.objects.filter(username__iexact=username):
            raise forms.ValidationError("A user with that username already exists.")
        return username


class StudentDetailsForm(forms.ModelForm):
    class Meta:
        model = StudentDetails
        fields = ["matnum", "course"]


class ConfirmStudentDetailsForm(forms.ModelForm):
    ownwork_confirmed = forms.BooleanField(
        help_text=lambda: markdown(config.OWNWORK_DECLARATION),
        required=True,
    )

    class Meta:
        model = StudentDetails
        fields = ["matnum", "ownwork_confirmed"]


class UserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name"]
