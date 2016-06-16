import logging
import re
import zipfile
from io import BytesIO
from os.path import join, split
from urllib.parse import unquote

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone

from inloop.core.sendfile import sendfile
from inloop.tasks.models import (CheckerResult, Task, TaskCategory,
                                 TaskSolution, TaskSolutionFile)
from inloop.tasks.docker import Checker


logger = logging.getLogger(__name__)


def error(request, message):
    return render(request, 'tasks/message.html', {
        'type': 'danger',
        'message': message
    })


@login_required
def category(request, slug):
    category = get_object_or_404(TaskCategory, slug=slug)
    tasks = Task.objects.filter(
        category=category,
        publication_date__lt=timezone.now()
    )
    return render(request, 'tasks/category.html', {
        'category': category,
        'tasks': tasks
    })


def index(request):
    if request.user.is_authenticated():
        progress = lambda a, b: (u_amt / t_amt) * 100 if t_amt != 0 else 0
        queryset = TaskCategory.objects.all()
        categories = []
        for o in queryset:
            t_amt = o.published_tasks().count()
            u_amt = o.completed_tasks_for_user(request.user).count()
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

    if task.publication_date > timezone.now():
        return redirect("/")

    if request.method == 'POST':
        manual_uploads = request.FILES.getlist('manual-upload')

        if not manual_uploads:
            return error(request, "No files provided.")

        if task.deadline_date and timezone.now() > task.deadline_date:
            return error(request, "This task has already expired!")

        solution_files = []
        for uploaded_file in manual_uploads:
            # this is only quick and dirty hack
            if not uploaded_file.name.endswith(".java"):
                return error(request, "Invalid files uploaded (allowed: *.java)")

            solution_files.append(
                TaskSolutionFile(filename=uploaded_file.name, file=uploaded_file)
            )

        solution = TaskSolution.objects.create(
            submission_date=timezone.now(),
            author=request.user,
            task=task
        )
        solution.tasksolutionfile_set = solution_files

        Checker(solution).start()

        return redirect("%s#your-solutions" % reverse("tasks:detail", kwargs={"slug": slug}))

    latest_solutions = TaskSolution.objects \
        .filter(task=task, author=request.user) \
        .order_by('-submission_date')[:5]

    return render(request, 'tasks/task-detail.html', {
        'latest_solutions': latest_solutions,
        'user': request.user,
        'title': task.title,
        'deadline_date': task.deadline_date,
        'description': task.description,
        'slug': task.slug
    })


# FIXME: this should be async as well
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

    solution_files = {}
    for solution_file in TaskSolutionFile.objects.filter(solution=solution):
        try:
            with open(solution_file.file_path(), encoding="utf-8", errors="replace") as f:
                solution_files[solution_file.filename] = f.read()
        except FileNotFoundError:
            logger.error("Dangling TaskSolutionFile(id=%d) detected" % solution_file.id)

    cr = get_object_or_404(CheckerResult, solution=solution)
    result = cr.stdout

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
