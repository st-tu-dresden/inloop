from django.contrib import admin

from inloop.solutions.models import Solution, SolutionFile
from inloop.solutions.statistics import Statistics


class SolutionFileInline(admin.StackedInline):
    model = SolutionFile
    readonly_fields = ['file']
    max_num = 0


@admin.register(Solution)
class SolutionAdmin(admin.ModelAdmin):
    class Media:
        css = {
            "all": []
        }
        js = ["js/Chart.min.js"]

    change_list_template = "admin/solutions/solutions.html"
    inlines = [SolutionFileInline]
    list_display = ['id', 'author', 'task', 'submission_date', 'passed', 'site_link']
    list_filter = ['passed', 'task__category', 'submission_date', 'task']
    search_fields = [
        'author__username', 'author__email', 'author__first_name', 'author__last_name'
    ]
    readonly_fields = ['task', 'submission_date', 'task', 'author', 'passed']

    def site_link(self, obj):
        return '<a href="%s">%s details</a>' % (obj.get_absolute_url(), obj)

    def changelist_view(self, request, extra_context=None):
        # Filter our admin view by the selected viewport filter
        solutions = Solution.objects.filter(**request.GET.dict())
        statistics = Statistics(solutions)
        extra = {
            'statistics': statistics,
        }
        if extra_context is not None:
            extra.update(extra_context)
        return super().changelist_view(request, extra_context=extra)

    site_link.allow_tags = True
    site_link.short_description = "View on site"
