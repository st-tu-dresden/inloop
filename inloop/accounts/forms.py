from django import forms
from django.contrib.auth import get_user_model, password_validation

from registration.forms import RegistrationFormUniqueEmail

from inloop.accounts.models import StudentDetails


class SignupForm(RegistrationFormUniqueEmail):
    # Workaround for Django ticket #26097 until 1.11 is released:
    # We need to override this field to include the help text of the
    # configured AUTH_PASSWORD_VALIDATORS.
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        strip=False,
        help_text=password_validation.password_validators_help_text_html()
    )


class StudentDetailsForm(forms.ModelForm):
    class Meta:
        model = StudentDetails
        fields = ["matnum", "course"]


class UserChangeForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name"]
