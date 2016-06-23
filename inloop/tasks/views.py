import re
from os.path import join
from urllib.parse import unquote

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from inloop.core.sendfile import sendfile
from inloop.tasks.models import Task, TaskCategory


@login_required
def category(request, slug):
    category = get_object_or_404(TaskCategory, slug=slug)
    tasks = Task.objects \
        .filter(category=category, publication_date__lt=timezone.now()) \
        .order_by("publication_date", "title")
    have_deadlines = any(task.deadline_date for task in tasks)
    return render(request, 'tasks/category.html', {
        'category': category,
        'tasks': tasks,
        'have_deadlines': have_deadlines
    })


def index(request):
    if request.user.is_authenticated():
        progress = lambda a, b: (u_amt / t_amt) * 100 if t_amt != 0 else 0
        queryset = TaskCategory.objects.order_by("name")
        categories = []
        for o in queryset:
            t_amt = o.published_tasks().count()
            u_amt = o.completed_tasks_for_user(request.user).count()
            if t_amt > 0:
                categories.append((o, (t_amt, u_amt, progress(u_amt, t_amt))))

        return render(request, 'tasks/index.html', {
            'categories': categories
        })
    else:
        return render(request, 'registration/login.html', {
            'hide_login_link': True
        })


@login_required
def serve_attachment(request, slug, path):
    """
    Serve static files from a task subdirectory.

    Access is granted exclusively to whitelisted subdirectories.
    """
    if re.search("^(images|attachments)/", path) is None:
        raise PermissionDenied

    if ".." in unquote(path):
        raise PermissionDenied

    # translate the slug into the internal task name
    task = get_object_or_404(Task, slug=slug)
    filesystem_path = join(task.name, path)

    return sendfile(request, filesystem_path, settings.GIT_ROOT)
