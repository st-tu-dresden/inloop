from django.contrib import admin

from inloop.tasks.models import Category, Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['title', 'category']}),
        ('Date Information', {'fields': ['pubdate', 'deadline']}),
        ('Content', {'fields': ['description', 'slug']})
    ]
    list_display = ('title', 'category', 'pubdate', 'deadline')
    list_filter = ['pubdate', 'deadline', 'category']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}


admin.site.register(Category)
