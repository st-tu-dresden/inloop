from django import forms
from accounts.models import UserProfile
from accounts.models import CourseOfStudy as COS
from accounts.validators import validate_mat_num


class UserForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'autocomplete': 'off'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'autocomplete': 'off'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'autocomplete': 'off'}))
    course = forms.ModelChoiceField(queryset=COS.objects.all())
    mat_num = forms.IntegerField(widget=forms.NumberInput(attrs={
        'class': 'form-control',
        'autocomplete': 'off'}), validators=[validate_mat_num])

    class Meta(object):
        model = UserProfile
        fields = ('username', 'email', 'password', 'course', 'mat_num')


class NewCourseForm(forms.ModelForm):
    name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'off'
        })
    )

    class Meta(object):
        model = COS
        fields = ('name',)
