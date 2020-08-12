from django import template
from django.utils.functional import cached_property

from inloop.solutions.models import Solution

register = template.Library()


class ProgressInfo:
    """User submission progress information for Django templates."""

    def __init__(self, *, user, task):
        """Initialize progress info for the given user and task."""
        # using a queryset takes advantage of lazy evaluation
        self.queryset = Solution.objects.filter(author=user, task=task)
        self.task = task

    # cache it on our own, because count() is not cached by Django ORM
    @cached_property
    def current(self):
        """The current number of solutions."""
        return self.queryset.count()

    @property
    def limit(self):
        """The maximum number of submission for the task."""
        return self.task.submission_limit

    @property
    def has_limit(self):
        """True if the task has a submission limit."""
        return self.task.has_submission_limit

    @property
    def limit_reached(self):
        """True if the user can't submit more tasks."""
        if self.task.has_submission_limit:
            return self.current >= self.limit
        return False


@register.filter
def format_if(progress, format_str):
    """
    Format a ProgressInfo, but only if it has a submission limit.
    The format_str will be format()-ed with the following kwargs: `current` for the
    current number of submissions and `limit` for the submission limit.
    """
    if not isinstance(progress, ProgressInfo):
        raise ValueError('progress must be of type ProgressInfo')
    if progress.has_limit:
        return format_str.format(current=progress.current, limit=progress.limit)
    return ''


@register.simple_tag(takes_context=True)
def get_submission_progress(context, task):
    """Return progress information for a task."""
    return ProgressInfo(user=context['user'], task=task)
