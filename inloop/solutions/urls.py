from django.conf.urls import url

from inloop.solutions.views import (
    NewSolutionArchiveView,
    SideBySideEditorView,
    SolutionArchiveDownloadView,
    SolutionArchiveStatusView,
    SolutionDetailView,
    SolutionFileView,
    SolutionListView,
    SolutionStatusView,
    SolutionUploadView,
    StaffSolutionDetailView,
    get_last_checkpoint,
    mock_syntax_check,
    save_checkpoint,
)
from inloop.tasks.views import serve_attachment

app_name = "solutions"
urlpatterns = [
    url(r"^editor/(?P<slug_or_name>[-\w]+)/$", SideBySideEditorView.as_view(), name="editor"),
    url(r"^editor/(?P<slug>[-\w]+)/(?P<path>.*)$", serve_attachment, name="serve_attachment"),
    url(
        r"^detail/(?P<slug>[-\w]+)/(?P<scoped_id>[\d]+)/$",
        SolutionDetailView.as_view(),
        name="detail",
    ),
    url(r"^staffdetail/(?P<id>[\d]+)/$", StaffSolutionDetailView.as_view(), name="staffdetail"),
    url(r"^status/(?P<id>[\d]+)/$", SolutionStatusView.as_view(), name="status"),
    url(r"^file/(?P<pk>[\d]+)/$", SolutionFileView.as_view(), name="showfile"),
    url(r"^list/(?P<slug>[-\w]+)/$", SolutionListView.as_view(), name="list"),
    url(r"^upload/(?P<slug>[-\w]+)/$", SolutionUploadView.as_view(), name="upload"),
    url(
        r"^archive-status/(?P<solution_id>[\d]+)/$",
        SolutionArchiveStatusView.as_view(),
        name="archive_status",
    ),
    url(
        r"^create-archive/(?P<solution_id>[\d]+)/$",
        NewSolutionArchiveView.as_view(),
        name="archive_new",
    ),
    url(
        r"^download/(?P<solution_id>[-\w]+)/$",
        SolutionArchiveDownloadView.as_view(),
        name="archive_download",
    ),
    url(r"^checkpoint/save/(?P<slug>[-\w]+)/$", save_checkpoint, name="save-checkpoint"),
    url(r"^checkpoint/get/(?P<slug>[-\w]+)/$", get_last_checkpoint, name="get-last-checkpoint"),
    url(r"^syntax-check/$", mock_syntax_check, name="mock-syntax-check"),
]
