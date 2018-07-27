from django.contrib import admin, messages
from django.contrib.auth import get_user_model

from inloop.grading.admin import PlagiarismAdmin
from inloop.grading.copypasta import jplag_check_async
from inloop.tasks.models import Category, Task

User = get_user_model()


@admin.register(Task)
class TaskAdmin(PlagiarismAdmin):
    fieldsets = [(None, {
        'fields': ['title', 'category']
    }), ('Date Information', {
        'fields': ['pubdate', 'deadline']
    }), ('Content', {
        'fields': ['description', 'slug']
    })]
    list_display = ['title', 'category', 'pubdate', 'deadline']
    list_filter = ['pubdate', 'deadline', 'category']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title', )}
    actions = ['jplag_check_tasks']

    def jplag_check_tasks(self, request, queryset):
        """
        Admin action which starts a plagiarism check on the selected tasks.
        """
        jplag_check_async(users=User.objects.all(), tasks=queryset)
        msg = "The JPlag check has been started, please check the PlagiarismTests page."
        self.message_user(request, msg, messages.SUCCESS)

    jplag_check_tasks.short_description = 'Check selected tasks for plagiarism'


@admin.register(Category)
class CategoryAdmin(PlagiarismAdmin):
    list_display = ['name', 'display_order']
    list_filter = ['display_order']
    search_fields = ['name', 'display_order']
    prepopulated_fields = {'slug': ('name', )}
    actions = ['jplag_check_category']

    def jplag_check_category(self, request, queryset):
        """
        Admin action which starts a plagiarism check on the selected categories.
        """
        tasks = Task.objects.filter(category__in=queryset)
        jplag_check_async(users=User.objects.all(), tasks=tasks)
        msg = "The JPlag check has been started, please check the PlagiarismTests page."
        self.message_user(request, msg, messages.SUCCESS)

    jplag_check_category.short_description = 'Check selected categories for plagiarism'
