import json
from os.path import basename

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.views.generic import DetailView, View

from huey.exceptions import TaskLockedException

from inloop.solutions.models import Checkpoint, Solution, SolutionFile, create_archive_async
from inloop.solutions.prettyprint.checkstyle import (CheckstyleData, context_from_xml_strings,
                                                     xml_strings_from_testoutput)
from inloop.solutions.prettyprint.junit import checkeroutput_filter, xml_to_dict
from inloop.solutions.signals import solution_submitted
from inloop.solutions.validators import validate_filenames
from inloop.tasks.models import Task


class SolutionStatusView(LoginRequiredMixin, View):
    def get(self, request, id):
        solution = get_object_or_404(Solution, pk=id, author=request.user)
        return JsonResponse({'solution_id': solution.id, 'status': solution.status()})


class SubmissionError(Exception):
    pass


class SolutionSubmissionView(LoginRequiredMixin, View):
    def get_task(self, slug):
        task = get_object_or_404(Task.objects.published(), slug=slug)
        if task.is_expired:
            raise SubmissionError('The deadline for this task has passed.')
        return task

    def submit(self, files, author, task):
        if not files:
            raise SubmissionError("You haven't uploaded any files.")
        try:
            validate_filenames([f.name for f in files])
        except ValidationError as error:
            raise SubmissionError(str(error))
        with transaction.atomic():
            solution = Solution.objects.create(author=author, task=task)
            SolutionFile.objects.bulk_create([
                SolutionFile(solution=solution, file=f) for f in files
            ])
        solution_submitted.send(sender=self.__class__, solution=solution)


class SolutionEditorView(SolutionSubmissionView):
    def get(self, request, slug):
        return TemplateResponse(request, 'solutions/editor/editor.html', {
            'task': get_object_or_404(Task.objects.published(), slug=slug),
            'active_tab': 1
        })

    def post(self, request, slug):
        if not request.is_ajax():
            return JsonResponse({'success': False})
        try:
            task = self.get_task(slug)
            json_data = json.loads(request.body)
            uploads = json_data.get('uploads', {})
            files = [SimpleUploadedFile(f, c.encode()) for f, c in uploads.items()]
            self.submit(files, request.user, task)
        except (SubmissionError, json.JSONDecodeError):
            return JsonResponse({'success': False})
        return JsonResponse({'success': True})


class SolutionUploadView(SolutionSubmissionView):
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


class ModularEditorTabView(LoginRequiredMixin, View):
    def get(self, request, slug):
        tab_id = request.GET.get('tab_id')
        if not tab_id:
            raise Http404('No file name supplied to tab view.')
        return TemplateResponse(request, 'solutions/editor/modular_editor_tab.html', {
            'tab_id': tab_id,
        })


class ModalNotificationView(LoginRequiredMixin, View):
    def get(self, request, slug):
        title = request.GET.get('title')
        body = request.GET.get('body')
        hook = request.GET.get('hook')
        if not title or not body or not hook:
            raise Http404('No title or body or hook supplied to notification view.')
        return TemplateResponse(request, 'solutions/editor/modals/modal_notification.html', {
            'title': title,
            'body': body,
            'hook': hook
        })


class ModalInputView(LoginRequiredMixin, View):
    def get(self, request, slug):
        title = request.GET.get('title')
        placeholder = request.GET.get('placeholder')
        hook = request.GET.get('hook')
        input_hook = request.GET.get('input_hook')
        if not title or not placeholder or not hook or not input_hook:
            raise Http404('Insufficient data supplied to input view.')
        return TemplateResponse(request, 'solutions/editor/modals/modal_input_form.html', {
            'title': title,
            'placeholder': placeholder,
            'hook': hook,
            'input_hook': input_hook
        })


class ModalConfirmationView(LoginRequiredMixin, View):
    def get(self, request, slug):
        title = request.GET.get('title')
        hook = request.GET.get('hook')
        confirm_button_hook = request.GET.get('confirm_button_hook')
        cancel_button_hook = request.GET.get('cancel_button_hook')
        if not title or not hook or not confirm_button_hook or not cancel_button_hook:
            raise Http404('Insufficient data supplied to confirmation view.')
        return TemplateResponse(request, 'solutions/editor/modals/modal_confirmation_form.html', {
            'title': title,
            'hook': hook,
            'confirm_button_hook': confirm_button_hook,
            'cancel_button_hook': cancel_button_hook
        })


class NewSolutionArchiveView(LoginRequiredMixin, View):
    def get(self, request, solution_id):
        if not solution_id:
            raise Http404('No solution id was supplied.')
        solution = get_object_or_404(Solution, pk=solution_id, author=request.user)
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
        solution = get_object_or_404(Solution, pk=solution_id, author=request.user)
        if solution.archive:
            return JsonResponse({'status': 'available'})
        return JsonResponse({'status': 'unavailable'})


class SolutionArchiveDownloadView(LoginRequiredMixin, View):
    def get(self, request, solution_id):
        if not solution_id:
            raise Http404('No solution id was supplied.')
        solution = get_object_or_404(Solution, pk=solution_id, author=request.user)
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
            'active_tab': 3
        })


class SolutionDetailView(LoginRequiredMixin, View):
    def get_context_data(self):
        return {}

    def get_object(self, **kwargs):
        task = Task.objects.published().filter(slug=kwargs['slug'])
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
        return SolutionFile.objects.filter(solution__author=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['solution'] = self.object.solution
        return context


@login_required
def get_last_checkpoint(request, slug):
    if not request.is_ajax():
        return JsonResponse({'success': False})

    task = get_object_or_404(Task.objects.published(), slug=slug)

    checkpoints = Checkpoint.objects.filter(author=request.user, task=task)
    if not checkpoints.exists():
        return JsonResponse({'success': True, 'checkpoint': None})

    last_checkpoint = checkpoints.last()
    checkpoint_files = dict()
    for checkpoint_file in last_checkpoint.checkpointfile_set.all():
        checkpoint_files[checkpoint_file.name] = checkpoint_file.contents

    return JsonResponse({
        'success': True,
        'checkpoint': {
            'md5': str(last_checkpoint.md5),
            'files': checkpoint_files,
        }
    })


@login_required
def save_checkpoint(request, slug):
    if not request.is_ajax() or not request.method == 'POST':
        return JsonResponse({'success': False})

    task = get_object_or_404(Task.objects.published(), slug=slug)

    data = request.POST.get('checkpoint')
    if data is None:
        return JsonResponse({'success': False})

    # Load nested data from json
    data = json.loads(data)
    try:
        Checkpoint.objects.create_checkpoint(data, task, request.user)
    except ValueError:
        return JsonResponse({'success': False})

    return JsonResponse({'success': True})
