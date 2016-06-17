"""
Class based views to manage tasks, task categories and submitted solutions.
"""
from django import VERSION as DJANGO_VERSION
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import View
from django.contrib import messages
from django.utils import timezone

from inloop.tasks.models import check_solution, Task, TaskSolution, TaskSolutionFile
from inloop.tasks.prettyprint import junit


# Once we have upgraded to Django 1.9, we can use the shipped contrib.auth Mixins.
if DJANGO_VERSION >= (1, 9, 0):
    raise DeprecationWarning("LoginRequiredMixin is provided by Django")


def get_published_task_or_404(slug):
    task = get_object_or_404(Task, slug=slug)
    if not task.is_published():
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
            'task': get_published_task_or_404(slug=slug),
            'active_tab': 0
        })


class SolutionUploadView(LoginRequiredMixin, View):
    def get(self, request, slug):
        return render(request, "tasks/upload_form.html", {
            'task': get_published_task_or_404(slug=slug),
            'active_tab': 1
        })

    def post(self, request, slug):
        task = get_published_task_or_404(slug=slug)
        uploads = request.FILES.getlist('uploads')

        if not uploads:
            messages.error(request, "You haven't uploaded any files.")
            return redirect("tasks:solutionupload", slug=slug)

        if not all([f.name.endswith(".java") for f in uploads]):
            messages.error(request, "You have uploaded invalid files (allowed: *.java).")
            return redirect("tasks:solutionupload", slug=slug)

        with transaction.atomic():
            solution = TaskSolution.objects.create(
                author=request.user,
                task=task
            )
            solution.tasksolutionfile_set = [
                TaskSolutionFile(filename=f.name, file=f) for f in uploads
            ]

        check_solution(solution.id)
        messages.success(request, "Your solution has been submitted to the checker.")
        return redirect("tasks:solutionlist", slug=slug)


class SolutionListView(LoginRequiredMixin, View):
    def get(self, request, slug):
        task = get_published_task_or_404(slug=slug)
        solutions = TaskSolution.objects \
            .filter(task=task, author=request.user) \
            .order_by("-id")[:5]
        return render(request, "tasks/solutions.html", {
            'task': task,
            'solutions': solutions,
            'active_tab': 2
        })


class SolutionDetailView(LoginRequiredMixin, View):
    def get(self, request, solution_id):
        solution = get_object_or_404(TaskSolution, pk=solution_id)

        if not (solution.author == request.user or request.user.is_staff):
            raise Http404()

        if solution.status() == "pending":
            messages.info(request, "This solution is still being checked. Please try again later.")
            return redirect("tasks:solutionlist", slug=solution.task.slug)

        if solution.status() in ["lost", "error"]:
            messages.warning(
                request,
                "Sorry, but the server had trouble checking this solution. Please try "
                "to upload it again or contact the administrator if the problem persists."
            )
            return redirect("tasks:solutionlist", slug=solution.task.slug)

        # TODO: PrettyPrinters should be configurable (for now, we only have one for JUnit)
        result = solution.checkerresult_set.last()
        xml_reports = junit.checkeroutput_filter(result.checkeroutput_set)
        testsuites = [
            junit.xml_to_dict(xml) for xml in xml_reports
        ]

        return render(request, "tasks/solutiondetail.html", {
            'solution': solution,
            'result': result,
            'testsuites': testsuites
        })
