import re

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from constance import config
from django_registration import validators
from django_registration.forms import RegistrationForm

from inloop.accounts.models import StudentDetails
from inloop.common.templatetags.markdown import markdown

User = get_user_model()


class SignupForm(RegistrationForm):
    """
    A user-friendly sign-up form with dynamically configurable help texts and validation.

    The sign-up form checks for case-insensitive uniqueness of username and email in the
    clean_* methods. This way, the corresponding database queries are run after Django's
    built-in validators have blocked invalid values such as NUL.
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
        """
        Ensure the email is unique and check against pattern configured in the admin interface.
        """
        pattern = config.EMAIL_PATTERN
        email = self.cleaned_data["email"]
        if pattern:
            # The pattern is always validated in the admin interface by testing if
            # re.compile() succeeds. If it fails to compile now, there must be some
            # serious error which we can't fix here and it's better to crash.
            regex = re.compile(pattern, re.VERBOSE)
            if not regex.search(email):
                raise ValidationError(markdown(config.EMAIL_ERROR_MESSAGE))
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email

    def clean_username(self) -> str:
        """
        Ensure the username is unique.
        """
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exists():
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
