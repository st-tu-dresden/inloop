from django.shortcuts import render_to_response, redirect, get_object_or_404

from tasks.models import Task


def index(request):
	basic_tasks = Task.objects.filter(category='B')
	advanced_tasks = Task.objects.filter(category='A')
	lesson_tasks = Task.objects.filter(category='L')
	exam_tasks = Task.objects.filter(category='E')
	return render_to_response('tasks/index.html', {
			'basic_tasks' : basic_tasks,
			'advanced_tasks' : advanced_tasks,
			'lesson_tasks' : lesson_tasks,
			'exam_tasks' : exam_tasks,
		})

def detail(request, slug):
	task = get_object_or_404(Task, slug=slug)
	return render_to_response('tasks/task-detail.html', {
		'title' : task.title,
		'deadline_date' : task.deadline_date,
		'description' : task.description,
		})

def edit(request, slug):
	pass

def results(request, slug):
	pass