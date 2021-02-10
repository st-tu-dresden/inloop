from django.urls import path, re_path

from inloop.solutions.views import (
    NewSolutionArchiveView,
    SideBySideEditorView,
    SolutionArchiveDownloadView,
    SolutionArchiveStatusView,
    SolutionDetailView,
    SolutionFileView,
    SolutionListView,
    SolutionUploadView,
    StaffSolutionDetailView,
    get_last_checkpoint,
    mock_syntax_check,
    save_checkpoint,
    solution_status,
)
from inloop.tasks.views import serve_attachment

app_name = "solutions"
urlpatterns = [
    re_path(r"^editor/(?P<slug_or_name>[-\w]+)/$", SideBySideEditorView.as_view(), name="editor"),
    re_path(r"^editor/(?P<slug>[-\w]+)/(?P<path>.*)$", serve_attachment, name="serve_attachment"),
    path("detail/<slug:slug>/<int:scoped_id>/", SolutionDetailView.as_view(), name="detail"),
    path("staffdetail/<int:id>/", StaffSolutionDetailView.as_view(), name="staffdetail"),
    path("status/<int:id>/", solution_status, name="status"),
    path("file/<int:pk>/", SolutionFileView.as_view(), name="showfile"),
    path("list/<slug:slug>/", SolutionListView.as_view(), name="list"),
    path("upload/<slug:slug>/", SolutionUploadView.as_view(), name="upload"),
    path(
        "archive-status/<int:solution_id>/",
        SolutionArchiveStatusView.as_view(),
        name="archive_status",
    ),
    path(
        "create-archive/<int:solution_id>/",
        NewSolutionArchiveView.as_view(),
        name="archive_new",
    ),
    path(
        "download/<int:solution_id>/",
        SolutionArchiveDownloadView.as_view(),
        name="archive_download",
    ),
    path("checkpoint/save/<slug:slug>/", save_checkpoint, name="save-checkpoint"),
    path("checkpoint/get/<slug:slug>/", get_last_checkpoint, name="get-last-checkpoint"),
    path("syntax-check/", mock_syntax_check, name="mock-syntax-check"),
]
