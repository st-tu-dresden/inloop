"""
Views to manage tasks and task categories and submitted solutions.

"""

import re
from os.path import join
from urllib.parse import unquote

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils import timezone
from django.views.generic import View

from inloop.common.sendfile import sendfile
from inloop.tasks.models import Category, Task


def get_published_task_or_404(slug):
    task = get_object_or_404(Task, slug=slug)
    if not task.is_published():
        raise Http404
    return task


def index(request):
    if request.user.is_anonymous:
        return TemplateResponse(request, "registration/login.html", {"hide_login_link": True})

    def progress(m, n):
        return m / n * 100 if n != 0 else 0

    categories = []

    for category in Category.objects.order_by("name"):
        num_published = category.published_tasks().count()
        num_completed = category.completed_tasks_for_user(request.user).count()
        if num_published > 0:
            categories.append(
                (category, (num_published, num_completed, progress(num_completed, num_published)))
            )

    return TemplateResponse(request, "tasks/index.html", {"categories": categories})


@login_required
def category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    tasks = Task.objects \
        .filter(category=category, publication_date__lt=timezone.now()) \
        .order_by("publication_date", "title")
    have_deadlines = any(task.deadline_date for task in tasks)
    return TemplateResponse(request, 'tasks/category.html', {
        'category': category,
        'tasks': tasks,
        'have_deadlines': have_deadlines
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


class TaskDetailView(LoginRequiredMixin, View):
    def get(self, request, slug):
        return TemplateResponse(request, "tasks/detail.html", {
            'task': get_published_task_or_404(slug=slug),
            'active_tab': 0
        })
