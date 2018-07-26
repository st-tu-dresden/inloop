from django.contrib import admin
from django.contrib.auth.models import User

from inloop.grading.admin import PlagiarismAdmin
from inloop.grading.copypasta import jplag_check_async
from inloop.tasks.models import Category, Task


def jplag_check_tasks(modeladmin, request, queryset):
    """
    Synchronous function to check selected tasks in admin model with JPlag.
    """
    users = User.objects.all()
    jplag_check_async(users=users, tasks=queryset)
    modeladmin.message_user(
        request, "The jplag check has been dispatched. Please check again later."
    )


def jplag_check_category(modeladmin, request, queryset):
    """
    Synchronous convenience function to check selected categories in the
    admin model with JPlag.
    """
    tasks = Task.objects.filter(category__in=queryset)
    jplag_check_tasks(modeladmin, request, tasks)


jplag_check_tasks.short_description = 'Check tasks for plagiarism'
jplag_check_category.short_description = 'Check category for plagiarism'


@admin.register(Task)
class TaskAdmin(PlagiarismAdmin):
    fieldsets = [
        (None, {'fields': ['title', 'category']}),
        ('Date Information', {'fields': ['pubdate', 'deadline']}),
        ('Content', {'fields': ['description', 'slug']})
    ]
    list_display = ('title', 'category', 'pubdate', 'deadline')
    list_filter = ['pubdate', 'deadline', 'category']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}

    actions = [jplag_check_tasks]


@admin.register(Category)
class CategoryAdmin(PlagiarismAdmin):
    list_display = ('name', 'display_order')
    list_filter = ['display_order']
    search_fields = ['name', 'display_order']
    prepopulated_fields = {'slug': ('name',)}

    actions = [jplag_check_category]
