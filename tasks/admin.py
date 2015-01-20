from django.contrib import admin
from tasks.models import Task, TaskFile


class TaskFileInline(admin.TabularInline):
    model = TaskFile
    extra = 1


# exclude = ('content',)

class TaskAdmin(admin.ModelAdmin):
    fieldsets = [(None, {'fields': ['title', 'author', 'category']}),
                 ('Date Information', {'fields': ['publication_date', 'deadline_date']}),
                 ('Content', {'fields': ['description', 'slug']})]
    list_display = ('title', 'publication_date', 'deadline_date', 'author')
    list_filter = ['category', 'publication_date', 'deadline_date']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [TaskFileInline]


admin.site.register(Task, TaskAdmin)
