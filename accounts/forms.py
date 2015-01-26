from django import forms
from accounts.models import UserProfile
from accounts.validators import validate_mat_num


class UserForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    mat_num = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control'}), validators=[validate_mat_num])

    class Meta:
        model = UserProfile
        fields = ('username', 'email', 'password', 'mat_num'
        )