from django.contrib import admin
from django.urls import reverse

from inloop.tasks.models import (CheckerOutput, CheckerResult, Task,
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
    list_display = ('id', 'author', 'task', 'submission_date', 'passed', 'site_link')
    list_filter = ['passed', 'task']
    search_fields = [
        'author__username',
        'author__email',
        'author__first_name',
        'author__last_name'
    ]
    readonly_fields = ('task', 'submission_date', 'task', 'author', 'passed')

    def site_link(self, obj):
        return '<a href="%s">%s details</a>' % (obj.get_absolute_url(), obj)

    site_link.allow_tags = True
    site_link.short_description = "View on site"


class CheckerOutputInline(admin.TabularInline):
    model = CheckerOutput
    readonly_fields = ('result', 'name', 'output')
    max_num = 0


class CheckerResultAdmin(admin.ModelAdmin):
    inlines = [
        CheckerOutputInline
    ]
    list_display = ('id', 'linked_solution', 'created_at', 'runtime', 'return_code', 'is_success')
    list_filter = ['return_code']
    readonly_fields = (
        'linked_solution', 'created_at', 'runtime',
        'return_code', 'is_success', 'stdout', 'stderr'
    )
    exclude = ('passed', 'time_taken', 'solution')

    def linked_solution(self, obj):
        link = reverse("admin:tasks_tasksolution_change", args=[obj.solution_id])
        return '<a href="%s">%s</a>' % (link, obj.solution)

    linked_solution.allow_tags = True
    linked_solution.short_description = "Solution"


admin.site.register(CheckerResult, CheckerResultAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(TaskCategory)
admin.site.register(TaskSolution, TaskSolutionAdmin)
