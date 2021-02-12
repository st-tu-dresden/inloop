from __future__ import annotations

import json
from json import JSONDecodeError
from os.path import basename
from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import ObjectDoesNotExist, Q
from django.db.models.query import QuerySet
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, View

from constance import config
from huey.exceptions import TaskLockedException

from inloop.solutions.models import (
    Checkpoint,
    Solution,
    SolutionFile,
    SubmissionError,
    create_archive_async,
    create_checkpoint,
    submit,
)
from inloop.solutions.prettyprint.junit import checkeroutput_filter, xml_to_dict
from inloop.tasks.models import FileTemplate, Task


class HttpResponseBadJsonRequest(JsonResponse):
    """Response that indicates an invalid JSON request made by the client."""

    status_code = 400

    def __init__(self) -> None:
        super().__init__({"error": "invalid json"})


@login_required
def solution_status(request: HttpRequest, id: int) -> HttpResponse:
    """
    Return the JSON encoded status for the given solution. The solution list
    view contains Javascript that polls this endpoint asynchronously.
    """
    solution = get_object_or_404(Solution, pk=id, author=request.user)
    return JsonResponse({"solution_id": solution.id, "status": solution.status()})


def get_visible_task_or_404(user: User, slug: str) -> Task:
    """
    Return the task identified by the slug if it exists and if it is visible
    for the given user, raise Http404 otherwise.
    """
    return get_object_or_404(Task.objects.published().visible_by(user=user), slug=slug)


def _is_valid_file_item(item: Any) -> bool:
    """Return True if the given file item conforms to the expected schema."""
    return (
        isinstance(item, dict)
        and isinstance(item.get("name"), str)
        and isinstance(item.get("contents"), str)
    )


def parse_json_payload(payload: bytes) -> Dict[str, Any]:
    """Unwrap and validate the JSON encoded file payload."""
    data = json.loads(payload)
    if not (
        isinstance(data, dict)
        and isinstance(data.get("files"), list)
        and all(_is_valid_file_item(item) for item in data["files"])
    ):
        raise ValidationError("invalid data")
    return data


def _get_layout_preference(request: HttpRequest) -> str:
    """Determine which editor view the user prefers (i.e., used last time)."""
    layout = request.COOKIES.get("layout")
    if layout not in ["editor", "upload", "taskonly"]:
        layout = "editor"
    return layout


class SideBySideEditorView(LoginRequiredMixin, View):
    # with never_cache we instruct the browser to fetch fresh data
    # even when this view is accessed via the back button
    @method_decorator(never_cache)
    def get(self, request: HttpRequest, slug_or_name: str) -> HttpResponse:
        """
        Show the side-by-side editor for the task referenced by slug or system_name.
        Requests with a non-slug url are redirected to their slug url equivalent.
        """
        qs = Task.objects.published().visible_by(user=request.user)
        try:
            task = qs.filter(Q(slug=slug_or_name) | Q(system_name=slug_or_name)).get()
        except ObjectDoesNotExist:
            raise Http404
        if slug_or_name != task.slug:
            return HttpResponseRedirect(reverse("solutions:editor", args=[task.slug]))
        context = {
            "task": task,
            "syntax_check_endpoint": config.SYNTAX_CHECK_ENDPOINT,
            "layout": _get_layout_preference(request),
        }
        return TemplateResponse(request, "solutions/editor.html", context)

    def post(self, request: HttpRequest, slug_or_name: str) -> HttpResponse:
        """
        Handle JSON-encoded POST submission requests from the side-by-side editor.
        """
        try:
            # if it's a name and not a slug, get_visible_task_or_404(…) will make it fail with 404
            task = get_visible_task_or_404(request.user, slug_or_name)
            data = parse_json_payload(request.body)
            create_checkpoint(data["files"], task, request.user)
            files = [
                SimpleUploadedFile(file["name"], file["contents"].encode())
                for file in data["files"]
            ]
            submit(files, request.user, task)
            if not task.has_submission_limit:
                return JsonResponse({"success": True})
            return JsonResponse(
                {
                    "success": True,
                    "submission_limit": task.submission_limit,
                    "num_submissions": Solution.objects.filter(
                        author=request.user, task=task
                    ).count(),
                }
            )
        except ValidationError as error:
            # flake8 warning B306 doesn't apply here, because ValidationError
            # declares the "message" attribute explicitly
            return JsonResponse(
                {"success": False, "saved": False, "reason": error.message}  # noqa: B306
            )
        except SubmissionError as error:
            return JsonResponse({"success": False, "saved": True, "reason": str(error)})
        except JSONDecodeError:
            return HttpResponseBadJsonRequest()


class SolutionUploadView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, slug: str) -> HttpResponse:
        try:
            task = get_visible_task_or_404(request.user, slug)
            files = request.FILES.getlist("uploads", default=[])
            submit(files, request.user, task)
        except SubmissionError as error:
            messages.error(request, str(error))
            return redirect("solutions:editor", slug_or_name=slug)
        except ValidationError as error:
            messages.error(request, error.message)  # noqa: B306
            return redirect("solutions:editor", slug_or_name=slug)
        messages.success(request, "Your solution has been submitted.")
        return redirect("solutions:list", slug=slug)


def access_solution_or_404(user: User, solution_id: int) -> Solution:
    """
    Access a solution with a given user.

    Regular users should only be able to access solution objects
    they authored. When a regular user tries to access another
    user's solution, a Http 404 error is raised. Since staff
    members however should be able to view other users'
    solutions, this restriction does not apply to them.
    """
    if user.is_staff:
        return get_object_or_404(Solution, pk=solution_id)
    return get_object_or_404(Solution, pk=solution_id, author=user)


class NewSolutionArchiveView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, solution_id: int) -> HttpResponse:
        solution = access_solution_or_404(request.user, solution_id)
        if solution.archive:
            return JsonResponse({"status": "available"})
        try:
            create_archive_async(solution)
        except TaskLockedException:
            return JsonResponse({"status": "already running"})
        return JsonResponse({"status": "initiated"})


class SolutionArchiveStatusView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, solution_id: int) -> HttpResponse:
        solution = access_solution_or_404(request.user, solution_id)
        if solution.archive:
            return JsonResponse({"status": "available"})
        return JsonResponse({"status": "unavailable"})


class SolutionArchiveDownloadView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, solution_id: int) -> HttpResponse:
        solution = access_solution_or_404(request.user, solution_id)
        if solution.archive:
            response = HttpResponse(solution.archive, content_type="application/zip")
            attachment = "attachment; filename=%s" % basename(solution.archive.name)
            response["Content-Disposition"] = attachment
            return response
        return redirect("solutions:detail", slug=solution.task.slug, scoped_id=solution.scoped_id)


class SolutionListView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, slug: str) -> HttpResponse:
        task = get_object_or_404(Task.objects.published(), slug=slug)
        solutions = (
            Solution.objects.select_related("task")
            .filter(task=task, author=request.user)
            .order_by("-id")[:5]
        )
        return TemplateResponse(
            request,
            "solutions/solution_list.html",
            {
                "task": task,
                "solutions": solutions,
            },
        )


class SolutionDetailView(LoginRequiredMixin, View):
    def get_context_data(self) -> Dict[str, Any]:
        return {}

    def get_object(self, **kwargs: Any) -> Solution:
        task = get_object_or_404(Task.objects.published(), slug=kwargs["slug"])
        self.solution = get_object_or_404(
            Solution, author=self.request.user, task=task, scoped_id=kwargs["scoped_id"]
        )
        return self.solution

    def get(self, request: HttpRequest, **kwargs: Any) -> HttpResponse:
        solution = self.get_object(**kwargs)

        if not config.IMMEDIATE_FEEDBACK:
            context = {"solution": solution, "files": solution.solutionfile_set.all()}
            context.update(self.get_context_data())
            return TemplateResponse(request, "solutions/solution_info.html", context)

        if solution.status() == "pending":
            messages.info(request, "This solution is still being checked. Please try again later.")
            return redirect("solutions:list", slug=solution.task.slug)

        if solution.status() in ["lost", "error"]:
            messages.warning(
                request,
                "Sorry, but the server had trouble checking this solution. Please try "
                "to upload it again or contact the administrator if the problem persists.",
            )
            return redirect("solutions:list", slug=solution.task.slug)

        result = solution.testresult_set.last()

        xml_reports_junit = checkeroutput_filter(result.testoutput_set)
        testsuites = [xml_to_dict(xml) for xml in xml_reports_junit]

        context = {
            "solution": solution,
            "result": result,
            "testsuites": testsuites,
            "files": solution.solutionfile_set.all(),
            "requested_archive": kwargs.get("requested_archive"),
        }
        context.update(self.get_context_data())

        return TemplateResponse(request, "solutions/solution_detail.html", context)


class StaffSolutionDetailView(UserPassesTestMixin, SolutionDetailView):
    def test_func(self) -> bool:
        return self.request.user.is_staff

    def get_context_data(self) -> Dict[str, Any]:
        return {
            "impersonate": self.request.user != self.solution.author,
        }

    def get_object(self, **kwargs: Any) -> Solution:
        self.solution = get_object_or_404(Solution, pk=kwargs["id"])
        return self.solution


class SolutionFileView(LoginRequiredMixin, DetailView):
    context_object_name = "file"
    template_name = "solutions/file_detail.html"

    def get_queryset(self) -> QuerySet:
        if self.request.user.is_staff:
            return SolutionFile.objects.all()
        return SolutionFile.objects.filter(solution__author=self.request.user)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        if self.request.user != self.object.solution.author:
            context["impersonate"] = True
        context["solution"] = self.object.solution
        return context


@never_cache
@login_required
def get_last_checkpoint(request: HttpRequest, slug: str) -> HttpResponse:
    task = get_object_or_404(Task.objects.published(), slug=slug)
    last_checkpoint = Checkpoint.objects.filter(author=request.user, task=task).last()
    queryset = []
    if last_checkpoint:
        queryset = last_checkpoint.checkpointfile_set.order_by("id")
    if not queryset:
        queryset = FileTemplate.objects.filter(task=task)
    files = [{"name": _file.name, "contents": _file.contents} for _file in queryset]
    return JsonResponse({"success": True, "files": files})


@require_POST
@login_required
def save_checkpoint(request: HttpRequest, slug: str) -> HttpResponse:
    task = get_object_or_404(Task.objects.published(), slug=slug)
    try:
        files = parse_json_payload(request.body)["files"]
        create_checkpoint(files, task, request.user)
    except JSONDecodeError:
        return HttpResponseBadJsonRequest()
    except ValidationError as error:
        return JsonResponse({"success": False, "reason": error.message})  # noqa: B306
    return JsonResponse({"success": True})


@require_POST
@csrf_exempt
def mock_syntax_check(request: HttpRequest) -> HttpResponse:
    """Temporary endpoint that outputs some fake syntax check results."""
    if not (config.SYNTAX_CHECK_ENDPOINT and config.SYNTAX_CHECK_MOCK_VALUE):
        return JsonResponse({"success": False, "reason": "bad configuration"})
    try:
        mocked_data = json.loads(config.SYNTAX_CHECK_MOCK_VALUE)
        return JsonResponse(mocked_data)
    except JSONDecodeError:
        return HttpResponseBadJsonRequest()
