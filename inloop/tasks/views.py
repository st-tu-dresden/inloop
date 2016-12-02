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
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.views.generic import View

from inloop.common.sendfile import sendfile
from inloop.tasks.models import Category, Task


def index(request):
    if request.user.is_anonymous:
        return TemplateResponse(request, "registration/login.html", {"hide_login_link": True})

    categories = [
        (category, category.completion_info(request.user))
        for category in Category.objects.order_by("name")
    ]

    return TemplateResponse(request, "tasks/index.html", {"categories": categories})


@login_required
def category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    tasks = category.task_set.published().order_by("pubdate", "title")
    have_deadlines = any(task.deadline for task in tasks)
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
    filesystem_path = join(task.system_name, path)

    return sendfile(request, filesystem_path, settings.GIT_ROOT)


class TaskDetailView(LoginRequiredMixin, View):
    def get(self, request, slug):
        return TemplateResponse(request, "tasks/detail.html", {
            'task': get_object_or_404(Task.objects.published(), slug=slug),
            'active_tab': 0
        })
