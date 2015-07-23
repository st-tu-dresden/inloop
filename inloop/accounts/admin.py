from django.contrib import admin
from inloop.accounts.models import UserProfile, CourseOfStudy

# Register your models here.

admin.site.register(UserProfile)
admin.site.register(CourseOfStudy)
