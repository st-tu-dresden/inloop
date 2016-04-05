import re
import zipfile
from io import BytesIO
from os.path import join, split
from urllib.parse import unquote

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from inloop.core.sendfile import sendfile
from inloop.tasks import filesystem_utils as fsu
from inloop.tasks.models import (Checker, CheckerResult, Task, TaskCategory,
                                 TaskSolution, TaskSolutionFile)


@login_required
def category(request, short_id):
    cat = get_object_or_404(TaskCategory, short_id=short_id)
    task_list = Task.objects.filter(
        category=cat,
        publication_date__lt=timezone.now())

    return render(request, 'tasks/category.html', {
        'user': request.user,
        'name': cat.name,
        'task_list': task_list
    })


def index(request):
    if request.user.is_authenticated():
        progress = lambda a, b: (u_amt / t_amt) * 100 if t_amt != 0 else 0
        queryset = TaskCategory.objects.all()
        categories = []
        for o in queryset:
            t_amt = len(o.get_tasks())
            u_amt = len(o.completed_tasks_for_user(request.user))
            if t_amt > 0:
                categories.append((o, (t_amt, u_amt, progress(u_amt, t_amt))))

        return render(request, 'tasks/index.html', {
            'categories': categories
        })
    else:
        return render(request, 'registration/login.html', {
            'hide_login_link': True
        })


@login_required
def detail(request, slug):
    task = get_object_or_404(Task, slug=slug)

    if request.method == 'POST':
        if task.deadline_date and timezone.now() > task.deadline_date:
            return render(request, 'tasks/message.html', {
                'type': 'danger',
                'message': 'This task has already expired!'
            })

        solution = TaskSolution(
            submission_date=timezone.now(),
            author=request.user,
            task=task
        )
        solution.save()

        if request.FILES.getlist('manual-upload'):
            for file in request.FILES.getlist('manual-upload'):
                tsf = TaskSolutionFile(filename=file.name, solution=solution)
                tsf.file.save(
                    file.name,
                    ContentFile("".join([s.decode("utf-8") for s in file.chunks()]))
                )
                tsf.save()
        else:
            for param in request.POST:
                if param.startswith('content') and not param.endswith('-filename'):
                    tsf = TaskSolutionFile(
                        filename=request.POST[param + '-filename'],
                        solution=solution
                    )
                    tsf.file.save(tsf.filename, ContentFile(request.POST[param]))
                    tsf.save()

        c = Checker(solution)
        c.start()

    latest_solutions = TaskSolution.objects \
        .filter(task=task, author=request.user) \
        .order_by('-submission_date')[:5]

    return render(request, 'tasks/task-detail.html', {
        'file_dict': fsu.latest_solution_files(task, request.user.username),
        'latest_solutions': latest_solutions,
        'user': request.user,
        'title': task.title,
        'deadline_date': task.deadline_date,
        'description': task.description,
        'slug': task.slug
    })


@login_required
def get_solution_as_zip(request, slug, solution_id):
    ts = get_object_or_404(TaskSolution, id=solution_id, author=request.user)
    solution_files = TaskSolutionFile.objects.filter(solution=ts)

    filename = '{username}_{slug}_solution_{sid}.zip'.format(
        username=request.user.username,
        slug=slug,
        sid=solution_id
    )

    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = 'filename={}'.format(filename)

    buffer = BytesIO()
    zf = zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED)

    for tsf in solution_files:
        tsf_dir, tsf_name = split(join(settings.MEDIA_ROOT, tsf.file.name))
        zf.writestr(tsf_name, tsf.file.read())

    zf.close()
    buffer.flush()

    final_zip = buffer.getvalue()
    buffer.close()

    response.write(final_zip)

    return response


@login_required
def results(request, slug, solution_id):
    task = get_object_or_404(Task, slug=slug)
    solution = get_object_or_404(TaskSolution, task=task, id=solution_id, author=request.user)
    solution_files = fsu.solution_file_dict(solution)
    cr = get_object_or_404(CheckerResult, solution=solution)
    result = cr.result

    return(render(request, 'tasks/task-result.html', {
        'task': task,
        'solution': solution,
        'solution_files': solution_files,
        'result': result
    }))


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
    filesystem_path = join(task.name, path)

    return sendfile(request, filesystem_path, settings.GIT_ROOT)
