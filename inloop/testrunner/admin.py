from django.contrib import admin
from django.urls import reverse

from inloop.testrunner.models import TestOutput, TestResult


class TestOutputInline(admin.TabularInline):
    model = TestOutput
    readonly_fields = ['result', 'name', 'output']
    max_num = 0


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    inlines = [TestOutputInline]
    list_display = ['id', 'linked_solution', 'created_at', 'runtime', 'return_code', 'is_success']
    list_filter = ['return_code', 'created_at']
    readonly_fields = [
        'linked_solution', 'created_at', 'runtime', 'return_code', 'is_success', 'stdout', 'stderr'
    ]
    exclude = ['passed', 'time_taken', 'solution']

    def linked_solution(self, obj):
        link = reverse("admin:solutions_solution_change", args=[obj.solution_id])
        return '<a href="%s">%s</a>' % (link, obj.solution)

    linked_solution.allow_tags = True
    linked_solution.short_description = "Solution"
