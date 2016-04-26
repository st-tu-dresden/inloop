from django.contrib import admin

from inloop.tasks.models import (CheckerResult, CheckerOutput, Task,
                                 TaskCategory, TaskSolution, TaskSolutionFile)


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


class TaskSolutionFileInline(admin.StackedInline):
    model = TaskSolutionFile
    readonly_fields = ('filename', 'file')
    max_num = 0


class CheckerResultInline(admin.StackedInline):
    model = CheckerResult
    max_num = 0
    readonly_fields = ('is_success', 'runtime', 'stdout', 'stderr')
    exclude = ('passed', 'return_code', 'time_taken')
    show_change_link = True

    def get_queryset(self, request):
        # show the latest CheckerResults first
        qs = super().get_queryset(request)
        return qs.order_by("-id")


class TaskSolutionAdmin(admin.ModelAdmin):
    inlines = [
        TaskSolutionFileInline,
        CheckerResultInline
    ]
    list_display = ('author', 'task', 'submission_date', 'passed')
    list_filter = ['passed', 'task']
    search_fields = [
        'author__username',
        'author__email',
        'author__first_name',
        'author__last_name'
    ]
    readonly_fields = ('task', 'submission_date', 'task', 'author', 'passed')


class CheckerOutputInline(admin.TabularInline):
    model = CheckerOutput
    readonly_fields = ('result', 'name', 'output')
    max_num = 0


class CheckerResultAdmin(admin.ModelAdmin):
    inlines = [
        CheckerOutputInline
    ]
    list_display = ('user', 'task', 'created_at', 'time_taken', 'return_code', 'passed')
    list_filter = ['passed']
    readonly_fields = ('solution', 'return_code', 'passed', 'stdout', 'stderr', 'time_taken')


admin.site.register(CheckerResult, CheckerResultAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(TaskCategory)
admin.site.register(TaskSolution, TaskSolutionAdmin)
