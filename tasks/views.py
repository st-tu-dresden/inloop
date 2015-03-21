from django.template.defaultfilters import slugify
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from tasks import forms
from tasks.models import Task
from . import filesystem_utils as fsu


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

    if request.method == 'POST':
        # TODO: save form data
        form = forms.UserEditorForm(request.POST)

    else:
        # TODO: prepopulate form with last saved data
        form = forms.UserEditorForm()

    return render(request, 'tasks/task-detail.html', {
        'editor_form': form,
        'file_dict': fsu.get_task_templates(task.title),
        'user': request.user,
        'title': task.title,
        'deadline_date': task.deadline_date,
        'description': task.description,
    })


@login_required
def edit(request, slug):
    # TODO: Separate options to add/ delete files
    task = get_object_or_404(Task, slug=slug)
    template_names = fsu.get_template_names(task.title)
    unittest_names = fsu.get_unittest_names(task.title)

    if request.method == 'POST':
        form = forms.ExerciseEditForm(request.POST,
                                      extra_templates=template_names,
                                      extra_unittests=unittest_names)
        if form.is_valid():
            # TODO: HANDLE FILE DELETION
            # populate direct task data
            task.title = form.data['e_title']
            # TODO: task.author = request.user,
            task.description = form.data['e_desc']
            task.publication_date = form.data['e_pub_date']
            task.deadline_date = form.data['e_dead_date']
            task.category = form.data['e_cat']
            task.slug = slugify(unicode(form.data['e_title']))
            task.save()
            return redirect('tasks:detail', slug=task.slug)
        else:
            print form.errors
    else:
        # construct data dict for pre populating form
        data_dict = {
            'e_title': task.title,
            'e_desc': task.description,
            'e_pub_date': task.publication_date,
            'e_dead_date': task.deadline_date,
            'e_cat': task.category
        }
        form = forms.ExerciseEditForm(initial=data_dict,
                                      extra_templates=template_names,
                                      extra_unittests=unittest_names)
        return render(request, 'tasks/edit_exercise.html', {
            'update_form': form
        })


@login_required
def delete(request, slug):
    task = get_object_or_404(Task, slug=slug)

    if request.method == 'POST':
        form = forms.ExerciseDeletionForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['are_you_sure']:
                task.delete()
                return redirect('tasks:index')
    else:
        form = forms.ExerciseDeletionForm()
        return render(request, 'tasks/delete_exercise.html', {
            'deletion_form': form,
            'task': task
        })


@login_required
def results(request, slug):
    pass


@login_required
def submit_new_exercise(request):
    if request.method == 'POST':
        # save form data
        form = forms.ExerciseSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            exercise_file_list = request.FILES.getlist('e_files')
            unittest_file_list = request.FILES.getlist('ut_files')
            for exercise_file in exercise_file_list:
                fsu.handle_uploaded_exercise(
                    exercise_file,
                    form.cleaned_data['e_title'])

            for unittest_file in unittest_file_list:
                fsu.handle_uploaded_unittest(
                    unittest_file,
                    form.cleaned_data['e_title'])

        # add Task object to system
        t = Task.objects.create(title=form.data['e_title'],
                                author=request.user,
                                description=form.data['e_desc'],
                                publication_date=form.data['e_pub_date'],
                                deadline_date=form.data['e_dead_date'],
                                category=form.data['e_cat'],
                                slug=slugify(unicode(form.data['e_title'])))
        t.save()
        return redirect('tasks:index')

    else:
        form = forms.ExerciseSubmissionForm()
        return render(request, 'tasks/new_exercise.html', {
            'exercise_form': form
        })
