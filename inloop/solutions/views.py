from __future__ import annotations

import json
import logging
from json import JSONDecodeError
from os.path import basename
from typing import Any, Dict, Iterable

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile, UploadedFile
from django.db import IntegrityError, transaction
from django.db.models import ObjectDoesNotExist, Q
from django.db.models.query import QuerySet
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, View

from constance import config
from huey.exceptions import TaskLockedException

from inloop.solutions.models import Checkpoint, Solution, SolutionFile, create_archive_async
from inloop.solutions.prettyprint.junit import checkeroutput_filter, xml_to_dict
from inloop.solutions.signals import solution_submitted
from inloop.solutions.validators import validate_filenames
from inloop.tasks.models import FileTemplate, Task

logger = logging.getLogger(__name__)


class HttpResponseBadJsonRequest(JsonResponse):
    """Response that indicates an invalid JSON request made by the client."""

    status_code = 400

    def __init__(self) -> None:
        super().__init__({"error": "invalid json"})


class SubmissionError(Exception):
    pass


@login_required
def solution_status(request: HttpRequest, id: int) -> JsonResponse:
    solution = get_object_or_404(Solution, pk=id, author=request.user)
    return JsonResponse({"solution_id": solution.id, "status": solution.status()})


class SolutionSubmitMixin:
    def get_task(self, request: HttpRequest, slug: str) -> Task:
        task = get_object_or_404(Task.objects.published().visible_by(user=request.user), slug=slug)
        if task.is_expired:
            raise SubmissionError("The deadline for this task has passed.")
        return task

    def submit(self, files: Iterable[UploadedFile], author: User, task: Task) -> None:
        if not files:
            raise SubmissionError("You haven't uploaded any files.")
        try:
            validate_filenames([file.name for file in files])
            self.check_submission_limit(author, task)
            solution = self.atomic_submit(files, author, task)
            if config.IMMEDIATE_FEEDBACK:
                solution_submitted.send(sender=self.__class__, solution=solution)
        except ValidationError as error:
            raise SubmissionError(str(error))
        except IntegrityError:
            logger.exception("db constraint violation occurred")
            raise SubmissionError("Concurrent submission is not possible.")

    def check_submission_limit(self, author: User, task: Task) -> None:
        """
        Ensure that the author is within the submission limit for the task (if any).
        """
        if task.has_submission_limit:
            count = Solution.objects.filter(author=author, task=task).count()
            limit = task.submission_limit
            if count >= limit:
                suffix = "" if limit == 1 else "s"
                raise SubmissionError(f"You cannot submit more than {limit} solution{suffix}.")

    @transaction.atomic()
    def atomic_submit(self, files: Iterable[UploadedFile], author: User, task: Task) -> Solution:
        solution = Solution.objects.create(author=author, task=task)
        SolutionFile.objects.bulk_create(
            [SolutionFile(solution=solution, file=file) for file in files]
        )
        return solution


def parse_submit_message(payload: bytes) -> Dict[str, Any]:
    """Unwrap and validate the JSON encoded submit message."""
    data = json.loads(payload)
    if not (isinstance(data, dict) and isinstance(data.get("uploads"), dict)):
        raise SubmissionError("invalid data")
    return data


class SideBySideEditorView(LoginRequiredMixin, SolutionSubmitMixin, View):
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
        return TemplateResponse(
            request,
            "solutions/editor.html",
            {"task": task, "syntax_check_endpoint": config.SYNTAX_CHECK_ENDPOINT},
        )

    def post(self, request: HttpRequest, slug_or_name: str) -> JsonResponse:
        """
        Handle JSON-encoded POST submission requests from the side-by-side editor.
        """
        try:
            # if it's a name and not a slug, get_task(…) will make it fail with 404
            task = self.get_task(request, slug_or_name)
            data = parse_submit_message(request.body)
            files = [
                SimpleUploadedFile(filename, content.encode())
                for filename, content in data["uploads"].items()
            ]
            self.submit(files, request.user, task)
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
        except SubmissionError as error:
            return JsonResponse({"success": False, "reason": str(error)})
        except JSONDecodeError:
            return HttpResponseBadJsonRequest()


class SolutionUploadView(LoginRequiredMixin, SolutionSubmitMixin, View):
    def get(self, request: HttpRequest, slug: str) -> HttpResponse:
        return TemplateResponse(
            request,
            "solutions/upload_form.html",
            {"task": get_object_or_404(Task.objects.published(), slug=slug), "active_tab": 2},
        )

    def post(self, request: HttpRequest, slug: str) -> HttpResponse:
        try:
            task = self.get_task(request, slug)
            files = request.FILES.getlist("uploads", default=[])
            self.submit(files, request.user, task)
        except SubmissionError as error:
            messages.error(request, str(error))
            return redirect("solutions:upload", slug=slug)
        messages.success(request, "Your solution has been submitted to the checker.")
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
    def get(self, request: HttpRequest, solution_id: int) -> JsonResponse:
        solution = access_solution_or_404(request.user, solution_id)
        if solution.archive:
            return JsonResponse({"status": "available"})
        try:
            create_archive_async(solution)
        except TaskLockedException:
            return JsonResponse({"status": "already running"})
        return JsonResponse({"status": "initiated"})


class SolutionArchiveStatusView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, solution_id: int) -> JsonResponse:
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
def get_last_checkpoint(request: HttpRequest, slug: str) -> JsonResponse:
    task = get_object_or_404(Task.objects.published(), slug=slug)
    last_checkpoint = Checkpoint.objects.filter(author=request.user, task=task).last()
    queryset = []
    if last_checkpoint:
        queryset = last_checkpoint.checkpointfile_set.order_by("id")
    if not queryset:
        queryset = FileTemplate.objects.filter(task=task)
    files = [{"name": _file.name, "contents": _file.contents} for _file in queryset]
    return JsonResponse({"success": True, "files": files})


@login_required
def save_checkpoint(request: HttpRequest, slug: str) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"success": False})
    task = get_object_or_404(Task.objects.published(), slug=slug)
    try:
        data = json.loads(request.body)
    except JSONDecodeError:
        return HttpResponseBadJsonRequest()
    try:
        Checkpoint.objects.save_checkpoint(data, task, request.user)
    except KeyError:
        return JsonResponse({"success": False})
    return JsonResponse({"success": True})


@csrf_exempt
def mock_syntax_check(request: HttpRequest) -> JsonResponse:
    """Temporary endpoint that outputs some fake syntax check results."""
    if request.method != "POST":
        return JsonResponse({"success": False})
    if not (config.SYNTAX_CHECK_ENDPOINT and config.SYNTAX_CHECK_MOCK_VALUE):
        return JsonResponse({"success": False, "reason": "bad configuration"})
    try:
        mocked_data = json.loads(config.SYNTAX_CHECK_MOCK_VALUE)
        return JsonResponse(mocked_data)
    except JSONDecodeError:
        return HttpResponseBadJsonRequest()
