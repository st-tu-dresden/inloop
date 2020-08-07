import json
import logging
from os.path import basename

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.db.models import ObjectDoesNotExist, Q
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.generic import DetailView, View

from huey.exceptions import TaskLockedException

from inloop.solutions.models import Checkpoint, Solution, SolutionFile, create_archive_async
from inloop.solutions.prettyprint.checkstyle import (CheckstyleData, context_from_xml_strings,
                                                     xml_strings_from_testoutput)
from inloop.solutions.prettyprint.junit import checkeroutput_filter, xml_to_dict
from inloop.solutions.signals import solution_submitted
from inloop.solutions.validators import validate_filenames
from inloop.tasks.models import Task

logger = logging.getLogger(__name__)


class SolutionStatusView(LoginRequiredMixin, View):
    def get(self, request, id):
        solution = get_object_or_404(Solution, pk=id, author=request.user)
        return JsonResponse({'solution_id': solution.id, 'status': solution.status()})


class SubmissionError(Exception):
    pass


class SolutionSubmitMixin:
    def get_task(self, slug):
        task = get_object_or_404(Task.objects.published(), slug=slug)
        if task.is_expired:
            raise SubmissionError('The deadline for this task has passed.')
        return task

    def submit(self, files, author, task):
        if not files:
            raise SubmissionError("You haven't uploaded any files.")
        try:
            validate_filenames([file.name for file in files])
            solution = self.atomic_submit(files, author, task)
            solution_submitted.send(sender=self.__class__, solution=solution)
        except ValidationError as error:
            raise SubmissionError(str(error))
        except IntegrityError:
            logger.exception('db constraint violation occurred')
            raise SubmissionError('Concurrent submission is not possible.')

    @transaction.atomic()
    def atomic_submit(self, files, author, task):
        solution = Solution.objects.create(author=author, task=task)
        SolutionFile.objects.bulk_create([
            SolutionFile(solution=solution, file=file) for file in files
        ])
        return solution


class SideBySideEditorView(LoginRequiredMixin, SolutionSubmitMixin, View):
    def get(self, request, slug_or_name):
        """
        Show the side-by-side editor for the task referenced by slug or system_name.
        Requests with a non-slug url are redirected to their slug url equivalent.
        """
        qs = Task.objects.published()
        try:
            task = qs.filter(Q(slug=slug_or_name) | Q(system_name=slug_or_name)).get()
        except ObjectDoesNotExist:
            raise Http404
        if slug_or_name != task.slug:
            return HttpResponseRedirect(reverse('solutions:editor', args=[task.slug]))
        return TemplateResponse(request, 'solutions/editor.html', {'task': task})

    def post(self, request, slug_or_name):
        """
        Handle JSON-encoded POST submissions requests from the side-by-side editor.
        """
        try:
            # if it's a name and not a slug, get_task(…) will make it fail with 404
            task = self.get_task(slug_or_name)
            json_data = json.loads(request.body)
            uploads = json_data.get('uploads', {})
            files = [
                SimpleUploadedFile(filename, content.encode())
                for filename, content in uploads.items()
            ]
            self.submit(files, request.user, task)
        except (SubmissionError, json.JSONDecodeError):
            return JsonResponse({'success': False})
        return JsonResponse({'success': True})


class SolutionUploadView(LoginRequiredMixin, SolutionSubmitMixin, View):
    def get(self, request, slug):
        return TemplateResponse(request, 'solutions/upload_form.html', {
            'task': get_object_or_404(Task.objects.published(), slug=slug),
            'active_tab': 2
        })

    def post(self, request, slug):
        try:
            task = self.get_task(slug)
            files = request.FILES.getlist('uploads', default=[])
            self.submit(files, request.user, task)
        except SubmissionError as error:
            messages.error(request, str(error))
            return redirect('solutions:upload', slug=slug)
        messages.success(request, 'Your solution has been submitted to the checker.')
        return redirect('solutions:list', slug=slug)


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
    def get(self, request, solution_id):
        if not solution_id:
            raise Http404('No solution id was supplied.')
        solution = access_solution_or_404(request.user, solution_id)
        if solution.archive:
            return JsonResponse({'status': 'available'})
        try:
            create_archive_async(solution)
        except TaskLockedException:
            return JsonResponse({'status': 'already running'})
        return JsonResponse({'status': 'initiated'})


class SolutionArchiveStatusView(LoginRequiredMixin, View):
    def get(self, request, solution_id):
        if not solution_id:
            raise Http404('No solution id was supplied.')
        solution = access_solution_or_404(request.user, solution_id)
        if solution.archive:
            return JsonResponse({'status': 'available'})
        return JsonResponse({'status': 'unavailable'})


class SolutionArchiveDownloadView(LoginRequiredMixin, View):
    def get(self, request, solution_id):
        if not solution_id:
            raise Http404('No solution id was supplied.')
        solution = access_solution_or_404(request.user, solution_id)
        if solution.archive:
            response = HttpResponse(solution.archive, content_type='application/zip')
            attachment = 'attachment; filename=%s' % basename(solution.archive.name)
            response['Content-Disposition'] = attachment
            return response
        return redirect('solutions:detail', slug=solution.task.slug, scoped_id=solution.scoped_id)


class SolutionListView(LoginRequiredMixin, View):
    def get(self, request, slug):
        task = get_object_or_404(Task.objects.published(), slug=slug)
        solutions = Solution.objects\
            .select_related('task')\
            .filter(task=task, author=request.user)\
            .order_by('-id')[:5]
        return TemplateResponse(request, 'solutions/solution_list.html', {
            'task': task,
            'solutions': solutions,
        })


class SolutionDetailView(LoginRequiredMixin, View):
    def get_context_data(self):
        return {}

    def get_object(self, **kwargs):
        task = get_object_or_404(Task.objects.published(), slug=kwargs['slug'])
        self.solution = get_object_or_404(
            Solution, author=self.request.user, task=task, scoped_id=kwargs['scoped_id']
        )
        return self.solution

    def get(self, request, **kwargs):
        solution = self.get_object(**kwargs)

        if solution.status() == 'pending':
            messages.info(request, 'This solution is still being checked. Please try again later.')
            return redirect('solutions:list', slug=solution.task.slug)

        if solution.status() in ['lost', 'error']:
            messages.warning(
                request,
                'Sorry, but the server had trouble checking this solution. Please try '
                'to upload it again or contact the administrator if the problem persists.'
            )
            return redirect('solutions:list', slug=solution.task.slug)

        result = solution.testresult_set.last()

        xml_reports_junit = checkeroutput_filter(result.testoutput_set)
        testsuites = [xml_to_dict(xml) for xml in xml_reports_junit]

        xml_strings_checkstyle = xml_strings_from_testoutput(
            testoutput_set=result.testoutput_set,
            startswith='checkstyle_errors',
            endswith='.xml'
        )

        if xml_strings_checkstyle:
            checkstyle_context = context_from_xml_strings(
                xml_strings=xml_strings_checkstyle, filter_keys=[])
            checkstyle_data = CheckstyleData(checkstyle_context, solution.solutionfile_set.all())
        else:
            checkstyle_data = None

        context = {
            'solution': solution,
            'result': result,
            'testsuites': testsuites,
            'checkstyle_data': checkstyle_data,
            'files': solution.solutionfile_set.all(),
            'requested_archive': kwargs.get('requested_archive')
        }
        context.update(self.get_context_data())

        return TemplateResponse(request, 'solutions/solution_detail.html', context)


class StaffSolutionDetailView(UserPassesTestMixin, SolutionDetailView):
    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self):
        return {
            'impersonate': self.request.user != self.solution.author,
        }

    def get_object(self, **kwargs):
        self.solution = get_object_or_404(Solution, pk=kwargs['id'])
        return self.solution


class SolutionFileView(LoginRequiredMixin, DetailView):
    context_object_name = 'file'
    template_name = 'solutions/file_detail.html'

    def get_queryset(self):
        if self.request.user.is_staff:
            return SolutionFile.objects.all()
        return SolutionFile.objects.filter(solution__author=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user != self.object.solution.author:
            context['impersonate'] = True
        context['solution'] = self.object.solution
        return context


@login_required
def get_last_checkpoint(request, slug):
    task = get_object_or_404(Task.objects.published(), slug=slug)

    checkpoints = Checkpoint.objects.filter(author=request.user, task=task)
    if not checkpoints.exists():
        return JsonResponse({'success': True, 'files': None})

    last_checkpoint = checkpoints.last()
    checkpoint_files = []
    for checkpoint_file in last_checkpoint.checkpointfile_set.order_by('id'):
        checkpoint_files.append({
            'name': checkpoint_file.name,
            'contents': checkpoint_file.contents
        })

    return JsonResponse({
        'success': True,
        'checksum': str(last_checkpoint.md5),
        'files': checkpoint_files,
    })


@login_required
def save_checkpoint(request, slug):
    if not request.method == 'POST':
        return JsonResponse({'success': False})

    task = get_object_or_404(Task.objects.published(), slug=slug)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False})

    try:
        Checkpoint.objects.save_checkpoint(data, task, request.user)
    except KeyError:
        return JsonResponse({'success': False})

    return JsonResponse({'success': True})
