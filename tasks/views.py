import zipfile
from io import StringIO
from os import path

from django.http import HttpResponse
from django.template.defaultfilters import slugify
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.utils import timezone
from django.conf import settings

from tasks import forms
from tasks.models import Task, TaskCategory, TaskSolution, TaskSolutionFile
from . import filesystem_utils as fsu


@login_required
def manage_categories(request):
    categories = TaskCategory.objects.all()
    return render(request, 'tasks/manage_categories.html', {
        'categories': categories
    })


@login_required
def delete_category(request, short_id):
    cat = get_object_or_404(TaskCategory, short_id=short_id)
    cat.delete()
    return redirect('tasks:man_cat')


@login_required
def edit_category(request, short_id):
    cat = get_object_or_404(TaskCategory, short_id=short_id)
    if request.method == 'POST':
        cat_form = forms.NewTaskCategoryForm(
            request.POST,
            request.FILES,
            instance=cat)
        if cat_form.is_valid():
            cat_form.save()
            return render(request, 'tasks/message.html', {
                'type': 'success',
                'message': 'The category has successfully been edited.'
            })
        # XXX: else?
    else:
        cat_form = forms.NewTaskCategoryForm(
            instance=cat,
            initial={
                'short_id': cat.short_id,
                'name': cat.name
            }
        )

    return render(request, 'tasks/edit_category.html', {
        'cat_form': cat_form,
        'short_id': short_id
    })


@login_required
def new_category(request):
    if request.method == 'POST':
        cat_form = forms.NewTaskCategoryForm(request.POST, request.FILES)
        if cat_form.is_valid():
            cat_form.save()
            return render(request, 'tasks/message.html', {
                'type': 'success',
                'message': 'The new category has been added to the system.'
            })
        # XXX: else?
    else:
        cat_form = forms.NewTaskCategoryForm()

    return render(request, 'tasks/new_category.html', {
        'cat_form': cat_form
    })


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
        progress = lambda a, b: u_amt / t_amt if t_amt != 0 else 0
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
            'show_login': True
        })


@login_required
def detail(request, slug):
    task = get_object_or_404(Task, slug=slug)

    if request.method == 'POST':
        if timezone.now() > task.deadline_date:
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
                # only allow .java files < 1Mb
                if file.content_type == 'text/x-java'\
                   and file.size < 1048576:
                    tsf = TaskSolutionFile(
                        filename=file.name,
                        solution=solution,
                    )

                    tsf.file.save(
                        file.name,
                        ContentFile(''.join([s for s in file.chunks()]))
                    )
        else:
            for param in request.POST:
                if param.startswith('content') \
                   and not param.endswith('-filename'):
                    tsf = TaskSolutionFile(
                        filename=request.POST[param + '-filename'],
                        solution=solution)

                    tsf.file.save(
                        tsf.filename,
                        ContentFile(request.POST[param]))
                    tsf.save()
    latest_solutions = TaskSolution.objects.filter(
        task=task,
        author=request.user)
    latest_solutions.order_by('-submission_date')[:5]

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

    buffer = StringIO()
    zf = zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED)

    for tsf in solution_files:
        tsf_dir, tsf_name = path.split(path.join(settings.MEDIA_ROOT, tsf.file.name))
        zf.writestr(tsf_name, tsf.file.read())

    zf.close()
    buffer.flush()

    final_zip = buffer.getvalue()
    buffer.close()

    response.write(final_zip)

    return response


@login_required
def edit(request, slug):
    task = get_object_or_404(Task, slug=slug)
    template_names = fsu.get_template_names(task.title)
    unittest_names = fsu.get_unittest_names(task.title)

    if request.method == 'POST':
        form = forms.ExerciseEditForm(
            request.POST,
            request.FILES,
            extra_templates=template_names,
            extra_unittests=unittest_names)
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

            for name, label, value in form.extra_templates():
                if form.cleaned_data[name]:
                    fsu.del_template(label, task.title)

            for name, label, value in form.extra_unittests():
                if form.cleaned_data[name]:
                    fsu.del_unittest(label, task.title)

            # populate direct task data
            cat = TaskCategory.objects.filter(
                short_id=form.cleaned_data['e_cat']
            )[0]
            task.title = form.cleaned_data['e_title']
            task.description = form.cleaned_data['e_desc']
            task.publication_date = form.cleaned_data['e_pub_date']
            task.deadline_date = form.cleaned_data['e_dead_date']
            task.category = cat
            task.slug = slugify(str(form.cleaned_data['e_title']))
            task.save()
            return redirect('tasks:detail', slug=task.slug)
        # XXX: else?
    else:
        # construct data dict for pre populating form
        data_dict = {
            'e_title': task.title,
            'e_desc': task.description,
            'e_pub_date': task.publication_date.strftime('%m/%d/%Y %H:%M'),
            'e_dead_date': task.deadline_date.strftime('%m/%d/%Y %H:%M'),
            'e_cat': str(task.category)
        }
        form = forms.ExerciseEditForm(
            initial=data_dict,
            extra_templates=template_names,
            extra_unittests=unittest_names)
    return render(request, 'tasks/edit_exercise.html', {
        'update_form': form
    })


@login_required
def delete(request, slug):
    task = get_object_or_404(Task, slug=slug)
    task.delete()
    return render(request, 'tasks/message.html', {
        'type': 'success',
        'message': 'The task has been deleted.'
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
            cat = TaskCategory.objects.filter(
                short_id=form.cleaned_data['e_cat']
            )[0]
            t = Task.objects.create(
                title=form.cleaned_data['e_title'],
                author=request.user,
                description=form.cleaned_data['e_desc'],
                publication_date=form.cleaned_data['e_pub_date'],
                deadline_date=form.cleaned_data['e_dead_date'],
                category=cat,
                slug=slugify(str(form.data['e_title'])))
            t.save()
            return render(request, 'tasks/message.html', {
                'type': 'success',
                'message': 'The task has successfully been created!'
            })

    else:
        form = forms.ExerciseSubmissionForm()

    return render(request, 'tasks/new_exercise.html', {
        'exercise_form': form
    })
