"""
Class based views to manage tasks, task categories and submitted solutions.
"""
from django import VERSION as DJANGO_VERSION
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import Http404, get_object_or_404, render
from django.views.generic import View

from inloop.tasks.models import Task, TaskSolution


# Once we have upgraded to Django 1.9, we can use the shipped contrib.auth Mixins.
if DJANGO_VERSION >= (1, 9, 0):
    raise DeprecationWarning("LoginRequiredMixin is provided by Django")


def get_active_task_or_404(slug):
    task = get_object_or_404(Task, slug=slug)
    if not task.is_active():
        raise Http404
    return task


class LoginRequiredMixin:
    """Class based view mixin similar to login_required() for ordinary views."""
    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        return login_required(view)


class SolutionStatusView(LoginRequiredMixin, View):
    def get(self, request, solution_id):
        solution = get_object_or_404(TaskSolution, pk=solution_id, author=request.user)
        return JsonResponse({'solution_id': solution.id, 'status': solution.status()})


class TaskDetailView(LoginRequiredMixin, View):
    def get(self, request, slug):
        return render(request, "tasks/detail.html", {
            'task': get_active_task_or_404(slug=slug)
        })
