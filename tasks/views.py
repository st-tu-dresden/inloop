from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from tasks import forms
from tasks.models import Task


@login_required
def index(request):
    basic_tasks = Task.objects.filter(category='B')
    advanced_tasks = Task.objects.filter(category='A')
    lesson_tasks = Task.objects.filter(category='L')
    exam_tasks = Task.objects.filter(category='E')
    return render(request, 'tasks/index.html', {
        'user': request.user,
        'basic_tasks': basic_tasks,
        'advanced_tasks': advanced_tasks,
        'lesson_tasks': lesson_tasks,
        'exam_tasks': exam_tasks,
    })


@login_required
def detail(request, slug):
    task = get_object_or_404(Task, slug=slug)
    task_file_list = task.task_files.all()

    if request.method == 'POST':
        # save form data
        form = forms.UserEditorForm(request.POST)
        for task_file in task_file_list:
            pass

    else:
        # prepopulate form with last saved data
        form = forms.UserEditorForm()

    return render(request, 'tasks/task-detail.html', {
        'editor_form': form,
        'task_files': task_file_list,
        'user': request.user,
        'title': task.title,
        'deadline_date': task.deadline_date,
        'description': task.description,
    })


@login_required
def edit(request, slug):
    pass


@login_required
def results(request, slug):
    pass
