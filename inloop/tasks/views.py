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
from django.db.models import ObjectDoesNotExist, Q
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.generic import View

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
    tasks = (
        category.task_set.published()
        .visible_by(user=request.user)
        .completed_by_values(request.user, order_by="pubdate")
    )
    unpublished_tasks = (
        category.task_set.unpublished()
        .visible_by(user=request.user)
        .completed_by_values(request.user, order_by="pubdate")
    )
    have_deadlines = any(task.deadline for task in tasks)
    return TemplateResponse(
        request,
        "tasks/category.html",
        {
            "category": category,
            "tasks": tasks,
            "unpublished_tasks": unpublished_tasks,
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


class TaskDetailView(LoginRequiredMixin, View):
    """
    Show the task description referenced by slug or system_name.

    Requests with a non-slug url are redirected to their slug url equivalent.
    """

    def get(self, request: HttpRequest, slug_or_name: str) -> HttpResponse:
        qs = Task.objects.published().visible_by(user=request.user)
        try:
            task = qs.filter(Q(slug=slug_or_name) | Q(system_name=slug_or_name)).get()
        except ObjectDoesNotExist:
            raise Http404

        if slug_or_name != task.slug:
            return HttpResponseRedirect(reverse("tasks:detail", args=[task.slug]))

        return TemplateResponse(request, "tasks/detail.html", {"task": task, "active_tab": 0})
