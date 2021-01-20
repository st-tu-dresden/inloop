from os.path import basename
from typing import Dict, Optional

from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse

from inloop.grading.models import DetectedPlagiarism, PlagiarismTest


class PlagiarismAdmin(admin.ModelAdmin):
    """
    Convenience model for the plagiarism testing frontend.

    Adds a plagiarism test information bar by simple inheritance.
    Can be used by admin models associated with Plagiarism tests,
    such as the Task/Solutions interfaces.
    """

    change_list_template = "admin/tasks/plagiarism.html"

    def changelist_view(
        self, request: HttpRequest, extra_context: Optional[Dict] = None
    ) -> HttpResponse:
        last_plagiarism_test = PlagiarismTest.objects.last()
        extra = {
            "test": last_plagiarism_test,
        }
        if extra_context is not None:
            extra.update(extra_context)
        return super().changelist_view(request, extra_context=extra)


@admin.register(DetectedPlagiarism)
class DetectedPlagiarismsAdmin(PlagiarismAdmin):
    list_display = ["test", "veto"]


@admin.register(PlagiarismTest)
class PlagiarismTestsAdmin(PlagiarismAdmin):
    list_display = ["id", "created_at", "command", "all_detected_plagiarisms"]
    actions = PlagiarismAdmin.actions + ["download_jplag_zip"]

    def download_jplag_zip(self, request: HttpRequest, queryset: QuerySet) -> HttpResponse:
        """
        Fetch the stored JPlag zip file and return it as a download.
        """
        if len(queryset) != 1:
            msg = "You can only download one zip file at a time."
            self.message_user(request, msg, messages.WARNING)
            return None
        zip_file = queryset[0].zip_file
        if not zip_file:
            msg = "The selected test has no downloadable zip file."
            self.message_user(request, msg, messages.WARNING)
            return None
        with open(zip_file.path, mode="rb") as stream:
            response = HttpResponse(stream, content_type="application/zip")
        attachment = "attachment; filename=%s" % basename(zip_file.path)
        response["Content-Disposition"] = attachment
        return response

    download_jplag_zip.short_description = "Download JPlag output as zip"
