from django import forms
from django.contrib.auth import get_user_model

from inloop.accounts.models import StudentDetails


class StudentDetailsForm(forms.ModelForm):
    class Meta:
        model = StudentDetails
        fields = ["matnum", "course"]


class UserChangeForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name"]
