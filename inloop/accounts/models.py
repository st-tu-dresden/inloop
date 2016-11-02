from django.conf import settings
from django.contrib.auth import models as auth_models
from django.contrib.sites.shortcuts import get_current_site
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.crypto import get_random_string

from inloop.accounts.validators import validate_mat_num


def next_week():
    """To be used as the default activation key expiration time."""
    return timezone.now() + timezone.timedelta(weeks=1)


class CourseOfStudy(models.Model):
    """Represents the course of study of the respective user."""

    class Meta:
        verbose_name_plural = "Courses of study"

    name = models.CharField(max_length=50, help_text="The course name", unique=True)

    def __str__(self):
        return self.name


class UserProfile(auth_models.AbstractUser):
    """Extended user model with support for course of studies."""

    # Length of the random key
    KEY_LENGTH = 40

    # FIXME: use activation key which encodes expiration
    activation_key = models.CharField(
        max_length=KEY_LENGTH,
        help_text="Random key used to verify the user's email",
        blank=True
    )
    key_expires = models.DateTimeField(
        default=next_week,
        blank=True,
        help_text="The key's deprecation time"
    )
    mat_num = models.IntegerField(
        help_text="Matriculation number",
        null=True,
        validators=[validate_mat_num]
    )
    course = models.ForeignKey(CourseOfStudy, null=True, on_delete=models.CASCADE)

    def generate_activation_key(self):
        self.activation_key = get_random_string(length=self.KEY_LENGTH)

    def activate(self):
        success = False
        if self.key_expires > timezone.now():
            self.is_active = True
            success = True

        self.activation_key = ''
        self.save()
        return success

    def send_activation_mail(self, request):
        context = {
            "request": request,
            "site": get_current_site(request),
            "user": self
        }
        subject = render_to_string("registration/activation_email_subject.txt", context=context)
        # force the subject to a single line
        subject = "".join(subject.splitlines())
        message = render_to_string("registration/activation_email.txt", context=context)
        self.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)


def get_system_user():
    """Return a UserProfile to be used for system tasks (e.g., imports)."""
    return UserProfile.objects.get_or_create(username="system")[0]
