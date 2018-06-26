from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.views.generic import DetailView, View

from inloop.solutions.models import Solution, SolutionFile
from inloop.solutions.prettyprint.tools import (CheckstyleData, checkeroutput_filter,
                                                context_from_xml_strings,
                                                xml_strings_from_testoutput, xml_to_dict)
from inloop.solutions.signals import solution_submitted
from inloop.tasks.models import Task


class SolutionStatusView(LoginRequiredMixin, View):
    def get(self, request, id):
        solution = get_object_or_404(Solution, pk=id, author=request.user)
        return JsonResponse({'solution_id': solution.id, 'status': solution.status()})


class SolutionUploadView(LoginRequiredMixin, View):
    def get(self, request, slug):
        return TemplateResponse(request, "solutions/upload_form.html", {
            'task': get_object_or_404(Task.objects.published(), slug=slug),
            'active_tab': 1
        })

    def post(self, request, slug):
        task = get_object_or_404(Task.objects.published(), slug=slug)
        redirect_to_upload = redirect("solutions:upload", slug=slug)

        if task.is_expired:
            messages.error(request, "The deadline for this task has passed.")
            return redirect_to_upload

        uploads = request.FILES.getlist('uploads')

        if not uploads:
            messages.error(request, "You haven't uploaded any files.")
            return redirect_to_upload

        if not all([f.name.endswith(".java") for f in uploads]):
            messages.error(request, "You have uploaded invalid files (allowed: *.java).")
            return redirect_to_upload

        with transaction.atomic():
            solution = Solution.objects.create(
                author=request.user,
                task=task
            )
            SolutionFile.objects.bulk_create([
                SolutionFile(solution=solution, file=upload) for upload in uploads
            ])

        solution_submitted.send(sender=self.__class__, solution=solution)
        messages.success(request, "Your solution has been submitted to the checker.")
        return redirect("solutions:list", slug=slug)


class SolutionListView(LoginRequiredMixin, View):
    def get(self, request, slug):
        task = get_object_or_404(Task.objects.published(), slug=slug)
        solutions = Solution.objects \
            .select_related("task") \
            .filter(task=task, author=request.user) \
            .order_by("-id")[:5]
        return TemplateResponse(request, "solutions/solution_list.html", {
            'task': task,
            'solutions': solutions,
            'active_tab': 2
        })


class SolutionDetailView(LoginRequiredMixin, View):
    def get_context_data(self):
        return {}

    def get_object(self, **kwargs):
        task = Task.objects.published().filter(slug=kwargs["slug"])
        self.solution = get_object_or_404(
            Solution, author=self.request.user, task=task, scoped_id=kwargs["scoped_id"]
        )
        return self.solution

    def get(self, request, **kwargs):
        solution = self.get_object(**kwargs)

        if solution.status() == "pending":
            messages.info(request, "This solution is still being checked. Please try again later.")
            return redirect("solutions:list", slug=solution.task.slug)

        if solution.status() in ["lost", "error"]:
            messages.warning(
                request,
                "Sorry, but the server had trouble checking this solution. Please try "
                "to upload it again or contact the administrator if the problem persists."
            )
            return redirect("solutions:list", slug=solution.task.slug)

        result = solution.testresult_set.last()

        xml_reports_junit = checkeroutput_filter(result.testoutput_set)
        testsuites = [xml_to_dict(xml) for xml in xml_reports_junit]

        xml_strings_checkstyle = xml_strings_from_testoutput(
            testoutput_set=result.testoutput_set,
            startswith="checkstyle_errors",
            endswith=".xml"
        )

        checkstyle_context = context_from_xml_strings(
            xml_strings=xml_strings_checkstyle,
            filter_keys=[]
        )

        checkstyle_data = CheckstyleData(
            checkstyle_context, solution.solutionfile_set.all()
        )

        context = {
            'solution': solution,
            'result': result,
            'testsuites': testsuites,
            'checkstyle_data': checkstyle_data,
            'files': solution.solutionfile_set.all(),
        }
        context.update(self.get_context_data())

        return TemplateResponse(request, "solutions/solution_detail.html", context)


class StaffSolutionDetailView(UserPassesTestMixin, SolutionDetailView):
    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self):
        return {
            "impersonate": self.request.user != self.solution.author,
        }

    def get_object(self, **kwargs):
        self.solution = get_object_or_404(Solution, pk=kwargs["id"])
        return self.solution


class SolutionFileView(LoginRequiredMixin, DetailView):
    context_object_name = "file"
    template_name = "solutions/file_detail.html"

    def get_queryset(self):
        return SolutionFile.objects.filter(solution__author=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["solution"] = self.object.solution
        return context
