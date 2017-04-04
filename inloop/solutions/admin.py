from django.contrib import admin

from inloop.solutions.models import Solution, SolutionFile


class SolutionFileInline(admin.StackedInline):
    model = SolutionFile
    readonly_fields = ('file',)
    max_num = 0


@admin.register(Solution)
class SolutionAdmin(admin.ModelAdmin):
    inlines = [
        SolutionFileInline
    ]
    list_display = ('id', 'author', 'task', 'submission_date', 'passed', 'site_link')
    list_filter = ['passed', 'task__category', 'submission_date', 'task']
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
