from django.contrib import admin
from inloop.tasks.models import Task, TaskCategory


class TaskAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['title', 'author', 'category']}),
        ('Date Information', {'fields': ['publication_date',
                                         'deadline_date']}),
        ('Content', {'fields': ['description', 'slug']})
    ]
    list_display = ('title', 'publication_date', 'deadline_date', 'author')
    list_filter = ['publication_date', 'deadline_date']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}


admin.site.register(Task, TaskAdmin)
admin.site.register(TaskCategory)
