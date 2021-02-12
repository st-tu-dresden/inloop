"""
Views to manage tasks and task categories and submitted solutions.

"""

import re
from os.path import join
from urllib.parse import unquote

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse

from constance import config

from inloop.common.sendfile import sendfile
from inloop.tasks.models import Category, Task


@login_required
def index(request: HttpRequest) -> HttpResponse:
    exam_category_slug = config.EXAM_CATEGORY_SLUG
    if exam_category_slug:
        return category(request, exam_category_slug)
    return TemplateResponse(
        request,
        "tasks/index.html",
        {
            "categories": Category.objects.order_by("display_order", "name"),
        },
    )


@login_required
def category(request: HttpRequest, slug: str) -> HttpResponse:
    category = get_object_or_404(Category, slug=slug)
    tasks = category.task_set.visible_by(user=request.user).completed_by_values(
        request.user, order_by="pubdate"
    )
    have_deadlines = any(task.deadline for task in tasks)
    return TemplateResponse(
        request,
        "tasks/category.html",
        {
            "category": category,
            "tasks": tasks,
            "have_deadlines": have_deadlines,
            "show_progress": config.IMMEDIATE_FEEDBACK,
        },
    )


@login_required
def serve_attachment(request: HttpRequest, slug: str, path: str) -> HttpResponse:
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

    return sendfile(request, filesystem_path, settings.REPOSITORY_ROOT)
