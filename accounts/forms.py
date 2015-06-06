from django import forms
from accounts.models import UserProfile
from accounts.models import CourseOfStudy as COS
from accounts import validators as v


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
    password1 = forms.CharField(
        validators=[v.validate_password],
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'off'
        }))
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'off'
        }))
    course = forms.ModelChoiceField(
        queryset=COS.objects.all())
    mat_num = forms.IntegerField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'pattern': '[0-9]{7}',
            'maxlength': '7',
            'autocomplete': 'off'
        }),
        validators=[v.validate_mat_num])

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    class Meta(object):
        model = UserProfile
        fields = ('username',
                  'email',
                  'password1',
                  'password2',
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
        exclude = ('username', 'email', 'password1', 'password2')
        fields = ('mat_num', 'course')


class EmailForm(UserForm):
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        # remove unwanted fields
        for field in self.Meta.exclude:
            self.fields.pop(field)

    class Meta(UserForm.Meta):
        model = UserProfile
        exclude = ('username', 'password1', 'password2', 'mat_num', 'course')
        fields = ('email', )


class PasswordForm(UserForm):
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
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
        fields = ('old_password', 'password1', 'password2')


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
