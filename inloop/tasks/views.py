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
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.generic import View

from inloop.common.sendfile import sendfile
from inloop.tasks.models import Category, Task


@login_required
def index(request):
    categories = [
        (category, category.completion_info(request.user))
        for category in Category.objects.order_by("display_order", "name")
    ]
    return TemplateResponse(request, "tasks/index.html", {
        "categories": categories,
    })


@login_required
def category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    tasks = category.task_set.published().completed_by_values(
        request.user, "title"
    )
    unpublished_tasks = category.task_set.unpublished().completed_by_values(
        request.user, "title"
    )
    print(unpublished_tasks)
    have_deadlines = any(task.deadline for task in tasks)
    return TemplateResponse(request, 'tasks/category.html', {
        'category': category,
        'tasks': tasks,
        'unpublished_tasks': unpublished_tasks,
        'have_deadlines': have_deadlines,
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

    return sendfile(request, filesystem_path, settings.REPOSITORY_ROOT)


class TaskDetailView(LoginRequiredMixin, View):
    """
    Show the task description referenced by slug or system_name.

    Requests with a non-slug url are redirected to their slug url equivalent.
    """

    def get(self, request, slug_or_name):
        qs = Task.objects.published()
        try:
            task = qs.filter(Q(slug=slug_or_name) | Q(system_name=slug_or_name)).get()
        except ObjectDoesNotExist:
            raise Http404

        if slug_or_name != task.slug:
            return HttpResponseRedirect(reverse("tasks:detail", args=[task.slug]))

        return TemplateResponse(request, "tasks/detail.html", {"task": task, "active_tab": 0})
