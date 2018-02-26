from django.contrib import admin

from inloop.grading.models import DetectedPlagiarism, PlagiarismTest

admin.site.register(DetectedPlagiarism)
admin.site.register(PlagiarismTest)
