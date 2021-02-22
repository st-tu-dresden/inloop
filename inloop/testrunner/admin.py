from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from inloop.testrunner.models import TestOutput, TestResult


class TestOutputInline(admin.TabularInline):
    model = TestOutput
    readonly_fields = ["result", "name", "output"]
    max_num = 0


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    class Media:
        css = {"all": ["css/admin/testrunner.css"]}

    inlines = [TestOutputInline]
    list_display = ["id", "linked_solution", "created_at", "runtime", "return_code", "is_success"]
    list_filter = ["return_code", "created_at"]
    search_fields = [
        "stdout",
        "stderr",
        "solution__author__username",
        "solution__author__last_name",
    ]
    readonly_fields = [
        "linked_solution",
        "created_at",
        "runtime",
        "return_code",
        "is_success",
        "stdout",
        "stderr",
    ]
    exclude = ["time_taken", "solution"]

    def linked_solution(self, test_result: TestResult) -> str:
        solution_id = test_result.solution_id
        url = reverse("admin:solutions_solution_change", args=[solution_id])
        return format_html('<a href="{url}">{solution_id}</a>', url=url, solution_id=solution_id)

    linked_solution.admin_order_field = "solution_id"
    linked_solution.short_description = "Solution id"

    def runtime(self, test_result: TestResult) -> str:
        return f"{test_result.time_taken:.2f}"

    runtime.admin_order_field = "time_taken"
    runtime.short_description = "Runtime (seconds)"
