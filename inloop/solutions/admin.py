from datetime import datetime, timedelta, timezone

from django.contrib import admin
from django.utils.timezone import now

from inloop.solutions.models import Solution, SolutionFile
from inloop.solutions.statistics import Statistics


class SolutionFileInline(admin.StackedInline):
    model = SolutionFile
    readonly_fields = ['file']
    max_num = 0


class SemesterFieldListFilter(admin.DateFieldListFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = "semester"
        self.links = self.generate_links()

    def generate_links(self):
        """Derive semesters of submitted solutions."""
        semesters = [('Any semester', {})]
        first_solution = Solution.objects.first()
        if not first_solution:
            return semesters

        # start and end are both in the CEST timezone
        tzinfo_cest = timezone(timedelta(hours=2))
        summer_start = datetime(2018, 4, 1, tzinfo=tzinfo_cest)
        winter_start = datetime(2018, 10, 1, tzinfo=tzinfo_cest)

        for year in range(first_solution.submission_date.year, now().year + 1):
            semesters.append(("Summer {}".format(year), {
                self.lookup_kwarg_since: str(summer_start.replace(year)),
                self.lookup_kwarg_until: str(winter_start.replace(year))
            }))
            semesters.append(("Winter {}/{}".format(year, year + 1), {
                self.lookup_kwarg_since: str(winter_start.replace(year)),
                self.lookup_kwarg_until: str(summer_start.replace(year=year + 1))
            }))
        return semesters


@admin.register(Solution)
class SolutionAdmin(admin.ModelAdmin):
    class Media:
        css = {"all": ["css/admin/solutions.css"]}
        js = ["js/Chart.min.js"]

    change_list_template = "admin/solutions/solutions.html"
    inlines = [SolutionFileInline]
    list_display = ['id', 'author', 'task', 'submission_date', 'passed', 'site_link']
    list_filter = [
        'passed',
        'task__category',
        ('submission_date', SemesterFieldListFilter),
        'submission_date',
        'task'
    ]
    search_fields = [
        'author__username', 'author__email', 'author__first_name', 'author__last_name'
    ]
    readonly_fields = ['task', 'submission_date', 'task', 'author', 'passed']

    def site_link(self, obj):
        return '<a href="%s">%s details</a>' % (obj.get_absolute_url(), obj)

    def changelist_view(self, request, extra_context=None):
        """Filter admin view by the selected viewport filter."""
        solutions = Solution.objects.filter(**request.GET.dict())
        extra = {}
        if solutions:
            extra["statistics"] = Statistics(solutions)
        if extra_context is not None:
            extra.update(extra_context)
        return super().changelist_view(request, extra_context=extra)

    site_link.allow_tags = True
    site_link.short_description = "View on site"
