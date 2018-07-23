from django.conf import settings
from django.contrib import messages
from django.contrib.auth.signals import user_logged_in
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import ObjectDoesNotExist
from django.dispatch import receiver
from django.urls import reverse
from django.utils.text import mark_safe

INCOMPLETE_HINT = (
    "Your user profile is incomplete. To ensure we can award bonus points to you, please "
    "set your name and matriculation number on <a href=\"%s\">My Profile</a>."
)


@receiver(user_logged_in, dispatch_uid="complete_profile_hint")
def complete_profile_hint(sender, user, request, **kwargs):
    """Show logged in users a hint if they do not have a complete profile."""
    if not user_profile_complete(user):
        message = mark_safe(INCOMPLETE_HINT % reverse("accounts:profile"))
        # fail_silently needs to be set for unit tests using RequestFactory
        messages.warning(request, message, fail_silently=True)


def user_profile_complete(user):
    """Return True if the given user has set matnum, first and last name."""
    try:
        return all((user.first_name, user.last_name, user.studentdetails.matnum))
    except ObjectDoesNotExist:
        return False


class Course(models.Model):
    """Course of study."""

    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.name


def default_course():
    course, _ = Course.objects.get_or_create(name="Other")
    return course.id


class StudentDetails(models.Model):
    """Associate additional data to the user account."""

    class Meta:
        verbose_name_plural = "Student details"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    matnum = models.CharField(
        blank=True, verbose_name="Matriculation number", max_length=20, validators=[
            RegexValidator(r'^[0-9]*$', "Please enter a numeric value or leave the field blank.")
        ]
    )
    course = models.ForeignKey(Course, default=default_course, on_delete=models.PROTECT)

    def __str__(self):
        return str(self.user)
