from django.contrib import admin

from inloop.tasks.models import (CheckerResult, Task, TaskCategory,
                                 TaskSolution, TaskSolutionFile)


class TaskAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['title', 'author', 'category']}),
        ('Date Information', {'fields': ['publication_date',
                                         'deadline_date']}),
        ('Content', {'fields': ['description', 'slug']})
    ]
    list_display = ('title', 'category', 'publication_date', 'deadline_date')
    list_filter = ['publication_date', 'deadline_date', 'category']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}


class TaskSolutionAdmin(admin.ModelAdmin):
    list_display = ('author', 'task', 'submission_date', 'passed')
    list_filter = ['passed']


admin.site.register(CheckerResult)
admin.site.register(Task, TaskAdmin)
admin.site.register(TaskCategory)
admin.site.register(TaskSolution, TaskSolutionAdmin)
admin.site.register(TaskSolutionFile)
