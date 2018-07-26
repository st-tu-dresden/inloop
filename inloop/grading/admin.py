
from django.contrib import admin
from django.http import HttpResponse

from inloop.grading.models import DetectedPlagiarism, PlagiarismTest


def download_jplag_zip(modeladmin, request, queryset):
    """Fetch the stored jplag zip file and return it as a download"""
    if len(queryset) != 1:
        modeladmin.message_user(
            request, "You can not download more or less than one zip file at a time."
        )
        return
    test = queryset[0]
    if not test.zip_file:
        modeladmin.message_user(
            request, "The selected plagiarism test has no downloadable zip file."
        )
    with open(test.zip_file.path, 'rb') as source:
        response = HttpResponse(source, content_type='application/zip')
    attachment = "attachment; filename={prefix}_{identifier}{file_type}".format_map({
        "prefix": "Jplag_Output",
        "identifier": str(test.created_at).replace(' ', '_'),
        "file_type": ".zip",
    })
    response[
        "Content-Disposition"
    ] = attachment
    return response


download_jplag_zip.short_description = "Download JPlag output as zip"


class PlagiarismAdmin(admin.ModelAdmin):
    """
    Convenience model for the plagiarism testing frontend.
    Adds a plagiarism test information bar by simple inheritance.
    Can be used by admin models associated with Plagiarism tests,
    such as the Task/Solutions interfaces.
    """
    change_list_template = 'admin/tasks/plagiarism.html'

    def changelist_view(self, request, extra_context=None):
        last_plagiarism_test = PlagiarismTest.objects.last()
        extra = {
            'test': last_plagiarism_test,
        }
        extra.update(extra_context or {})
        return super(PlagiarismAdmin, self).changelist_view(request, extra_context=extra)


@admin.register(DetectedPlagiarism)
class DetectedPlagiarismsAdmin(PlagiarismAdmin):
    list_display = (
        'test',
        'veto',
    )


@admin.register(PlagiarismTest)
class PlagiarismTestsAdmin(PlagiarismAdmin):
    list_display = (
        'id',
        'created_at',
        'command',
        'all_detected_plagiarisms',
    )

    actions = [download_jplag_zip]
