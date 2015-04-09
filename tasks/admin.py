from django.contrib import admin
from tasks.models import Task


# class TaskFileInline(admin.TabularInline):
#     model = TaskSolutionFile
#     extra = 1


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
#    inlines = [TaskFileInline]


admin.site.register(Task, TaskAdmin)
