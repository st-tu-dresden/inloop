from django.db import models

class Task(models.Model):
	title = models.CharField(max_length=100, help_text='Task name')
	author = models.CharField(max_length=100, help_text='Creator of task')
	description = models.TextField(help_text='Task description')
	publication_date = models.DateTimeField(help_text='When should the task be published?')
	deadline_date = models.DateTimeField(help_text='Date the task is due to')
	BASIC = 'B'
	ADVANCED = 'A'
	LESSON = 'L'
	EXAM = 'E'
	category = models.CharField(max_length=1,
								choices=(	(BASIC, 'Basic Exercise'),
											(ADVANCED, 'Advanced Exercise'),
											(LESSON, 'Lesson Exercise'),
											(EXAM, 'Exam Exercise')), help_text='Category of task')
	slug = models.SlugField(max_length=50, help_text='URL name')

	def task_is_active(self):
		'''
		Returns True if the task is already visible to the users.
		'''
		pass
		
