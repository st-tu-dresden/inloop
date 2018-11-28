import calendar

from django.contrib import admin
from django.utils import timezone

from inloop.solutions.models import Solution, SolutionFile
from inloop.solutions.statistics import Statistics


def start_of_summer_semester(year):
    return str(timezone.localdate(timezone.now()).replace(year=year, month=4, day=1))


def start_of_winter_semester(year):
    return str(timezone.localdate(timezone.now()).replace(year=year, month=10, day=1))


def start_of_month(year, month):
    return str(timezone.localdate(timezone.now()).replace(year=year, month=month, day=1))


def end_of_month(year, month):
    month = month % 12 + 1
    return str(timezone.localdate(timezone.now()).replace(year=year, month=month, day=1))


class SolutionFileInline(admin.StackedInline):
    model = SolutionFile
    readonly_fields = ['file']
    max_num = 0


class SemesterFieldListFilter(admin.DateFieldListFilter):
    def __init__(self, *args, **kwargs):
        super(SemesterFieldListFilter, self).__init__(*args, **kwargs)
        self.title = "semester"
        self.links = self.generate_links()

    def generate_links(self):
        """Derive semesters of submitted solutions."""
        solutions = Solution.objects.all().order_by("submission_date")
        if not solutions:
            return []
        first_solution_submission_date = solutions[0].submission_date.date()
        first_solution_year = first_solution_submission_date.year
        current_year = timezone.now().year
        semesters = []

        for year in range(first_solution_year, current_year + 1):
            semesters.append(("Summer Semester {}".format(year), {
                self.lookup_kwarg_since: start_of_summer_semester(year),
                self.lookup_kwarg_until: start_of_winter_semester(year)
            }))
            semesters.append(("Winter Semester {}".format(year), {
                self.lookup_kwarg_since: start_of_winter_semester(year),
                self.lookup_kwarg_until: start_of_summer_semester(year + 1)
            }))

        return semesters


class LastMonthsDateFieldFilter(admin.DateFieldListFilter):
    def __init__(self, *args, **kwargs):
        super(LastMonthsDateFieldFilter, self).__init__(*args, **kwargs)
        self.title = "month"
        self.links = list(self.links)
        self.links += self.generate_links()

    @staticmethod
    def get_last_months():
        solutions = Solution.objects.all()
        months = set()
        for solution in solutions:
            months.add((solution.submission_date.year, solution.submission_date.month))
        return months

    def generate_links(self):
        """Derive last 12 months."""
        months = []
        for (year, month) in LastMonthsDateFieldFilter.get_last_months():
            months.append(("{} {}".format(calendar.month_abbr[month], year), {
                self.lookup_kwarg_since: start_of_month(year, month),
                self.lookup_kwarg_until: end_of_month(year, month)
            }))
        return months


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
        ('submission_date', LastMonthsDateFieldFilter),
        'task'
    ]
    search_fields = [
        'author__username', 'author__email', 'author__first_name', 'author__last_name'
    ]
    readonly_fields = ['task', 'submission_date', 'task', 'author', 'passed']

    def site_link(self, obj):
        return '<a href="%s">%s details</a>' % (obj.get_absolute_url(), obj)

    def changelist_view(self, request, extra_context=None):
        """Filter admin view by the selected viewport filter"""
        solutions = Solution.objects.filter(**request.GET.dict())
        extra = {}
        if solutions:
            extra["statistics"] = Statistics(solutions)
        if extra_context is not None:
            extra.update(extra_context)
        return super().changelist_view(request, extra_context=extra)

    site_link.allow_tags = True
    site_link.short_description = "View on site"
