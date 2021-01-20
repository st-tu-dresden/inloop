"""
Bonus point grading specific to TU Dresden.
"""

import re
from datetime import datetime
from string import capwords
from typing import Callable, Iterable, Iterator, Tuple

from django.contrib.auth.models import User
from django.db.models import ObjectDoesNotExist
from django.utils.timezone import make_aware

from inloop.grading.models import get_ripoff_tasks_for_user
from inloop.tasks.models import Category


def get_user_data(user: User) -> Tuple[str, str, str, str, str, str]:
    """
    Return student data as a tuple (empty fields are guessed if possible).
    """
    try:
        matnum = user.studentdetails.matnum
        course = user.studentdetails.course
    except ObjectDoesNotExist:
        matnum = course = ""
    if not user.last_name:
        first_name, last_name = guess_name_from_email(user.email)
    else:
        first_name, last_name = user.first_name, user.last_name
    return (last_name, first_name, user.username, user.email, matnum, course)


def guess_name_from_email(email: str) -> Tuple[str, str]:
    """
    Try to guess first and last name from email and return it as a tuple.
    """
    name, domain = email.split("@", 1)
    if domain != "mailbox.tu-dresden.de":
        return "", ""
    first_name, last_name = name.split(".", 1)
    first_name = first_name.replace("_", " ")
    last_name = last_name.replace("_", " ")
    last_name = re.sub(r"[1-9]$", "", last_name)
    return capwords(first_name), capwords(last_name)


def points_for_completed_tasks(
    category_name: str, start_date: datetime, max_points: int
) -> Callable[[User], int]:
    """
    Return a function that calculates points based on the number of
    solved tasks in a category.

    Solutions are considered only if they were submitted after start_date.
    Points are limited by max_points.
    """
    category = Category.objects.get(name=category_name)
    start_date = make_aware(start_date)

    def func(user: User) -> int:
        points = len(
            category.task_set.exclude(id__in=get_ripoff_tasks_for_user(user))
            .filter(
                solution__passed=True,
                solution__author=user,
                solution__submission_date__gte=start_date,
            )
            .distinct()
        )
        return min(points, max_points)

    return func


def calculate_grades(users: Iterable[User], gradefunc: Callable[[User], int]) -> Iterator:
    """
    Generate a sequence of tuples with user data and the resulting grade using
    the given user query set and grading function.
    """
    for user in users:
        yield get_user_data(user) + (gradefunc(user),)
