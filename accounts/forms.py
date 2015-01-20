from django import forms
from accounts.models import UserProfile
from accounts.validators import validate_mat_num


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    mat_num = forms.IntegerField(validators=[validate_mat_num])

    class Meta:
        model = UserProfile
        fields = ('username', 'email', 'password', 'mat_num')