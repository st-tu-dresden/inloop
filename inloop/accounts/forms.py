from django import forms

from inloop.accounts.models import CourseOfStudy, UserProfile
from inloop.accounts.validators import validate_mat_num, validate_zih_mail

# HTML attributes used in all widgets
BASE_ATTRIBUTES = {
    "class": "form-control",
    "required": "required"
}

# base HTML attributes + autofocus for the first widget
AF_ATTRIBUTE = BASE_ATTRIBUTES.copy()
AF_ATTRIBUTE.update({
    "autofocus": "autofocus"
})


class UserForm(forms.ModelForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs=AF_ATTRIBUTE)
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs=BASE_ATTRIBUTES),
        validators=[validate_zih_mail]
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs=BASE_ATTRIBUTES)
    )
    password_repeat = forms.CharField(
        label='Confirm password',
        widget=forms.PasswordInput(attrs=BASE_ATTRIBUTES)
    )
    course = forms.ModelChoiceField(
        # TODO add hidden model attribute
        queryset=CourseOfStudy.objects.exclude(name__exact="Internal"),
        widget=forms.Select(attrs=BASE_ATTRIBUTES),
        empty_label=None
    )
    mat_num = forms.IntegerField(
        label='Matriculation number',
        widget=forms.TextInput(attrs=BASE_ATTRIBUTES),
        validators=[validate_mat_num]
    )

    def clean_password_repeat(self):
        password = self.cleaned_data.get("password")
        password_repeat = self.cleaned_data.get("password_repeat")
        if password and password_repeat and password != password_repeat:
            raise forms.ValidationError(
                "The two password fields do not match.",
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
