from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.views.generic import View

from inloop.solutions.models import Solution, SolutionFile
from inloop.solutions.prettyprint import junit
from inloop.tasks.models import Task
from inloop.testrunner.tasks import check_solution


# XXX: duplicated code
def get_published_task_or_404(slug):
    task = get_object_or_404(Task, slug=slug)
    if not task.is_published:
        raise Http404
    return task


class SolutionStatusView(LoginRequiredMixin, View):
    def get(self, request, solution_id):
        solution = get_object_or_404(Solution, pk=solution_id, author=request.user)
        return JsonResponse({'solution_id': solution.id, 'status': solution.status()})


class SolutionUploadView(LoginRequiredMixin, View):
    def get(self, request, slug):
        return TemplateResponse(request, "solutions/upload_form.html", {
            'task': get_published_task_or_404(slug=slug),
            'active_tab': 1
        })

    def post(self, request, slug):
        task = get_published_task_or_404(slug=slug)
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
            solution.solutionfile_set.set([
                SolutionFile(file=f) for f in uploads
            ], bulk=False, clean=True)

        check_solution(solution.id)
        messages.success(request, "Your solution has been submitted to the checker.")
        return redirect("solutions:list", slug=slug)


class SolutionListView(LoginRequiredMixin, View):
    def get(self, request, slug):
        task = get_published_task_or_404(slug=slug)
        solutions = Solution.objects \
            .filter(task=task, author=request.user) \
            .order_by("-id")[:5]
        return TemplateResponse(request, "solutions/solution_list.html", {
            'task': task,
            'solutions': solutions,
            'active_tab': 2
        })


class SolutionDetailView(LoginRequiredMixin, View):
    def get(self, request, solution_id):
        solution = get_object_or_404(Solution, pk=solution_id)

        if not (solution.author == request.user or request.user.is_staff):
            raise Http404()

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

        # TODO: PrettyPrinters should be configurable (for now, we only have one for JUnit)
        result = solution.testresult_set.last()
        xml_reports = junit.checkeroutput_filter(result.testoutput_set)
        testsuites = [
            junit.xml_to_dict(xml) for xml in xml_reports
        ]

        return TemplateResponse(request, "solutions/solution_detail.html", {
            'solution': solution,
            'result': result,
            'testsuites': testsuites
        })
