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
    """
    Base of all other forms that handle INLOOP user data.

    This form is used during account signup.
    """
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
    first_name = forms.CharField(
        widget=forms.TextInput(attrs=BASE_ATTRIBUTES)
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs=BASE_ATTRIBUTES)
    )

    def clean_password_repeat(self):
        """
        Check if the password confirmation field matches the password field.
        """
        password = self.cleaned_data.get("password")
        password_repeat = self.cleaned_data.get("password_repeat")
        if password and password_repeat and password != password_repeat:
            raise forms.ValidationError(
                "The two password fields do not match.",
                code='password_mismatch',
            )
        return password

    class Meta:
        model = UserProfile
        fields = (
            'username', 'first_name', 'last_name', 'email', 'password',
            'password_repeat', 'course', 'mat_num'
        )


class UserProfileForm(UserForm):
    """
    Form that will be used on the profile page.

    We don't want the user to change his username or email, and changing
    the password is handled in the PasswordForm.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # remove unwanted fields
        for field in self.Meta.exclude:
            self.fields.pop(field)

    class Meta(UserForm.Meta):
        model = UserProfile
        exclude = ('username', 'email', 'password', 'password_repeat')
        fields = ('first_name', 'last_name', 'mat_num', 'course')


class PasswordForm(UserForm):
    """
    Form that will be used on the "change password" page.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
