from django import forms
from inloop.accounts.models import UserProfile
from inloop.accounts.models import CourseOfStudy as COS
from inloop.accounts import validators as v


class UserForm(forms.ModelForm):
    error_messages = {
        'password_mismatch': 'The two password fields didn\'t match.',
    }
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'off'
        }))
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'autocomplete': 'off'
        }))
    password = forms.CharField(
        label='Password',
        validators=[v.validate_password],
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'off'
        }))
    password_repeat = forms.CharField(
        label='Confirm password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'off'
        }))
    course = forms.ModelChoiceField(
        queryset=COS.objects.all())
    mat_num = forms.IntegerField(
        label='Matriculation number',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'pattern': '[0-9]{7}',
            'maxlength': '7',
            'autocomplete': 'off'
        }),
        validators=[v.validate_mat_num])

    def clean_password(self):
        password = self.cleaned_data.get("password")
        password_repeat = self.cleaned_data.get("password_repeat")
        if password and password_repeat and password != password_repeat:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password

    class Meta(object):
        model = UserProfile
        fields = ('username',
                  'email',
                  'password',
                  'password_repeat',
                  'course',
                  'mat_num')


class UserProfileForm(UserForm):
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        # remove unwanted fields
        for field in self.Meta.exclude:
            self.fields.pop(field)

    class Meta(UserForm.Meta):
        model = UserProfile
        exclude = ('username', 'email', 'password', 'password_repeat')
        fields = ('mat_num', 'course')


class EmailForm(UserForm):
    def __init__(self, *args, **kwargs):
        super(EmailForm, self).__init__(*args, **kwargs)
        # remove unwanted fields
        for field in self.Meta.exclude:
            self.fields.pop(field)

    class Meta(UserForm.Meta):
        model = UserProfile
        exclude = ('username', 'password', 'password_repeat', 'mat_num', 'course')
        fields = ('email', )


class PasswordForm(UserForm):
    def __init__(self, *args, **kwargs):
        super(PasswordForm, self).__init__(*args, **kwargs)
        # remove unwanted fields
        for field in self.Meta.exclude:
            self.fields.pop(field)

    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'off'
        }))

    class Meta(UserForm.Meta):
        model = UserProfile
        exclude = ('username', 'email', 'mat_num', 'course')
        fields = ('old_password', 'password', 'password_repeat')


class NewCourseForm(forms.ModelForm):
    name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'off'
        }))

    class Meta(object):
        model = COS
        fields = ('name',)
