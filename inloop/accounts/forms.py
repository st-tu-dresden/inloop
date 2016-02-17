from django import forms

from inloop.accounts.models import UserProfile
from inloop.accounts.models import CourseOfStudy
from inloop.accounts.validators import validate_mat_num, validate_password


# HTML attributes used in all widgets
BASE_ATTRIBUTES = {
    "class": "form-control",
    "autocomplete": "off"
}


class UserForm(forms.ModelForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs=BASE_ATTRIBUTES)
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs=BASE_ATTRIBUTES)
    )
    password = forms.CharField(
        label='Password',
        validators=[validate_password],
        widget=forms.PasswordInput(attrs=BASE_ATTRIBUTES)
    )
    password_repeat = forms.CharField(
        label='Confirm password',
        widget=forms.PasswordInput(attrs=BASE_ATTRIBUTES)
    )
    course = forms.ModelChoiceField(
        queryset=CourseOfStudy.objects.all()
    )
    mat_num = forms.IntegerField(
        label='Matriculation number',
        widget=forms.TextInput(
            attrs=dict(BASE_ATTRIBUTES).update(pattern='[0-9]{7}', maxlength='7')
        ),
        validators=[validate_mat_num]
    )

    def clean_password_repeat(self):
        password = self.cleaned_data.get("password")
        password_repeat = self.cleaned_data.get("password_repeat")
        if password and password_repeat and password != password_repeat:
            raise forms.ValidationError(
                "The two password fields didn't match.",
                code='password_mismatch',
            )
        return password

    class Meta(object):
        model = UserProfile
        fields = (
            'username', 'email', 'password',
            'password_repeat', 'course', 'mat_num'
        )


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
        widget=forms.PasswordInput(attrs=BASE_ATTRIBUTES)
    )

    class Meta(UserForm.Meta):
        model = UserProfile
        exclude = ('username', 'email', 'mat_num', 'course')
        fields = ('old_password', 'password', 'password_repeat')


class NewCourseForm(forms.ModelForm):
    name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs=BASE_ATTRIBUTES)
    )

    class Meta(object):
        model = CourseOfStudy
        fields = ('name',)
