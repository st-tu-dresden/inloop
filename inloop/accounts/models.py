from datetime import timedelta
from random import choice
from typing import Any, Iterable, Sequence, Type

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, User
from django.contrib.auth.signals import user_logged_in
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import ObjectDoesNotExist
from django.dispatch import receiver
from django.http.request import HttpRequest
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

from constance import config

INCOMPLETE_HINT = (
    "Your user profile is incomplete. To ensure we can award bonus points to you, please "
    'set your name and matriculation number on <a href="%s">My Profile</a>.'
)


@receiver(user_logged_in, dispatch_uid="complete_profile_hint")
def complete_profile_hint(
    sender: Type[User], user: User, request: HttpRequest, **kwargs: Any
) -> None:
    """Show logged in users a hint if they do not have a complete profile."""
    if config.REQUIRE_OWNWORK_DECLARATION or user_profile_complete(user):
        return
    message = mark_safe(INCOMPLETE_HINT % reverse("accounts:profile"))
    # fail_silently needs to be set for unit tests using RequestFactory
    messages.warning(request, message, fail_silently=True)


def user_profile_complete(user: User) -> bool:
    """Return True if the given user has set matnum, first and last name."""
    try:
        return all((user.first_name, user.last_name, user.studentdetails.matnum))
    except ObjectDoesNotExist:
        return False


def prune_invalid_users() -> int:
    """
    Delete accounts that haven't been activated in time.
    Return the number of deleted accounts.
    """
    User = get_user_model()
    deadline = timezone.now() - timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS)
    invalid_users = User.objects.filter(
        date_joined__lte=deadline, is_active=False, last_login=None
    )
    _, removals_by_type = invalid_users.delete()
    return removals_by_type.get(settings.AUTH_USER_MODEL, 0)


@receiver(user_logged_in, dispatch_uid="assign_to_group_on_login")
def auto_assign_to_group(
    sender: Type[User], user: User, request: HttpRequest, **kwargs: Any
) -> None:
    """Automatically assign users without a group to a random group on login."""
    groups_to_assign = config.AUTO_ASSIGN_GROUPS
    if not groups_to_assign or user.groups.exists():
        return
    group_name = choice(groups_to_assign.split())
    try:
        user.groups.add(Group.objects.get(name=group_name))
    except Group.DoesNotExist:
        pass


def assign_to_groups(*, users: Iterable[User], groups: Sequence[Group]) -> int:
    """Randomly assign the given groups to the given users if they not already have a group."""
    num_assignments = 0
    for user in users:
        if user.groups.exists():
            continue
        user.groups.add(choice(groups))
        num_assignments += 1
    return num_assignments


class Course(models.Model):
    """Course of study."""

    name = models.CharField(max_length=64, unique=True)

    def __str__(self) -> str:
        return self.name


def default_course() -> int:
    course, _ = Course.objects.get_or_create(name="Other")
    return course.id


class StudentDetails(models.Model):
    """Associate additional data to the user account."""

    class Meta:
        verbose_name_plural = "Student details"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    matnum = models.CharField(
        blank=True,
        verbose_name="Matriculation number",
        max_length=20,
        validators=[
            RegexValidator(r"^[0-9]*$", "Please enter a numeric value or leave the field blank.")
        ],
    )
    course = models.ForeignKey(Course, default=default_course, on_delete=models.PROTECT)
    ownwork_confirmed = models.BooleanField(default=False)

    def __str__(self) -> str:
        return str(self.user)
