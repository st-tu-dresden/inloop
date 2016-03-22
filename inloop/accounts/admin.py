from django.contrib import admin

from inloop.accounts.models import CourseOfStudy, UserProfile

# Register your models here.

admin.site.register(UserProfile)
admin.site.register(CourseOfStudy)
