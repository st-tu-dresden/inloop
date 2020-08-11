from django import template

from inloop.solutions.models import Solution

register = template.Library()


@register.simple_tag(takes_context=True)
def submission_progress(context, format_str, task):
    """
    Return formatted progress info for a task, but only if it has a submission limit.
    The format_str will be format()-ed with the following kwargs: `current` for the
    current number of submissions and `limit` for the submission limit.
    """
    if not task.has_submission_limit:
        return ''
    num_submissions = Solution.objects.filter(author=context['user'], task=task).count()
    return format_str.format(current=num_submissions, limit=task.submission_limit)
