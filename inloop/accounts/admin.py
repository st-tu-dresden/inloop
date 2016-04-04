from django.contrib import admin

from inloop.accounts.models import CourseOfStudy, UserProfile


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'mat_num', 'is_staff', 'is_superuser', 'is_active')
    list_filter = ['is_active', 'is_staff', 'is_superuser']
    search_fields = ['last_name', 'email', 'mat_num']


admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(CourseOfStudy)
