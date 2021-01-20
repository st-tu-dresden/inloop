from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.text import Truncator

from inloop.grading.admin import PlagiarismAdmin
from inloop.grading.copypasta import jplag_check_async
from inloop.tasks.models import Category, FileTemplate, Task, TaskQuerySet

User = get_user_model()


@admin.register(Task)
class TaskAdmin(PlagiarismAdmin):
    fieldsets = [
        (None, {"fields": ["slug", "title", "category", "max_submissions", "group"]}),
        ("Date Information", {"fields": ["pubdate", "deadline"]}),
        ("Content", {"fields": ["description"]}),
    ]
    list_display = ["title", "category", "pubdate", "deadline"]
    list_filter = ["pubdate", "deadline", "category", "group"]
    search_fields = ["title", "description"]
    prepopulated_fields = {"slug": ("title",)}
    actions = PlagiarismAdmin.actions + ["jplag_check_tasks"]
    ordering = ["pubdate", "deadline", "title"]

    def jplag_check_tasks(self, request: HttpRequest, queryset: TaskQuerySet) -> None:
        """
        Admin action which starts a plagiarism check on the selected tasks.
        """
        jplag_check_async(users=User.objects.all(), tasks=queryset)
        msg = "The JPlag check has been started, please check the PlagiarismTests page."
        self.message_user(request, msg, messages.SUCCESS)

    jplag_check_tasks.short_description = "Check selected tasks for plagiarism"


@admin.register(Category)
class CategoryAdmin(PlagiarismAdmin):
    list_display = ["name", "display_order"]
    list_filter = ["display_order"]
    search_fields = ["name", "display_order"]
    prepopulated_fields = {"slug": ("name",)}
    actions = PlagiarismAdmin.actions + ["jplag_check_category"]

    def jplag_check_category(self, request: HttpRequest, queryset: QuerySet) -> None:
        """
        Admin action which starts a plagiarism check on the selected categories.
        """
        tasks = Task.objects.filter(category__in=queryset)
        jplag_check_async(users=User.objects.all(), tasks=tasks)
        msg = "The JPlag check has been started, please check the PlagiarismTests page."
        self.message_user(request, msg, messages.SUCCESS)

    jplag_check_category.short_description = "Check selected categories for plagiarism"


@admin.register(FileTemplate)
class FileTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "task", "contents_preview"]
    list_filter = ["task"]
    search_fields = ["name", "contents"]

    def contents_preview(self, file: FileTemplate) -> str:
        return Truncator(file.contents).chars(40)
