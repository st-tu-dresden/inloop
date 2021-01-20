from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Tuple, Type

from django.contrib import admin
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from inloop.solutions.models import Solution, SolutionFile


class SolutionFileInline(admin.StackedInline):
    model = SolutionFile
    readonly_fields = ["file"]
    max_num = 0


class SemesterListFilter(admin.SimpleListFilter):
    title = "semester"
    parameter_name = "semester"

    def lookups(
        self, request: HttpRequest, model_admin: Type[SolutionAdmin]
    ) -> List[Tuple[str, str]]:
        first_solution = Solution.objects.first()
        if not first_solution:
            return []
        last_solution = Solution.objects.last()
        start_year = first_solution.submission_date.year
        end_year = last_solution.submission_date.year
        lookups = []
        for year in range(start_year - 1, end_year + 1):
            lookups.extend(
                [(f"{year}s", f"Summer {year}"), (f"{year}w", f"Winter {year}/{year + 1}")]
            )
        return lookups

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        value = self.value()
        if not value:
            return queryset
        try:
            year = int(value[:-1])
        except ValueError:
            return queryset
        tzinfo_cest = timezone(timedelta(hours=2))
        summer_start = datetime(2018, 4, 1, tzinfo=tzinfo_cest)
        winter_start = datetime(2018, 10, 1, tzinfo=tzinfo_cest)
        if value.endswith("s"):
            return queryset.filter(
                submission_date__gte=summer_start.replace(year=year),
                submission_date__lt=winter_start.replace(year=year),
            )
        elif value.endswith("w"):
            return queryset.filter(
                submission_date__gte=winter_start.replace(year=year),
                submission_date__lt=summer_start.replace(year=year + 1),
            )
        return queryset


@admin.register(Solution)
class SolutionAdmin(admin.ModelAdmin):
    inlines = [SolutionFileInline]
    list_display = ["id", "author", "task", "submission_date", "passed", "site_link"]
    list_filter = ["passed", "task__category", SemesterListFilter, "submission_date", "task"]
    search_fields = [
        "author__username",
        "author__email",
        "author__first_name",
        "author__last_name",
    ]
    readonly_fields = ["task", "submission_date", "task", "author", "passed"]

    def site_link(self, obj: Solution) -> str:
        return format_html('<a href="{}">{}</a>', obj.get_absolute_url(), obj)

    site_link.short_description = "View on site"
