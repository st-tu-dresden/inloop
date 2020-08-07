from django.conf.urls import url

from inloop.solutions.views import (NewSolutionArchiveView, SideBySideEditorView,
                                    SolutionArchiveDownloadView, SolutionArchiveStatusView,
                                    SolutionDetailView, SolutionFileView, SolutionListView,
                                    SolutionStatusView, SolutionUploadView,
                                    StaffSolutionDetailView, get_last_checkpoint, save_checkpoint)
from inloop.tasks.views import serve_attachment

app_name = 'solutions'
urlpatterns = [
    url(
        r'^editor/(?P<slug_or_name>[-\w]+)/$',
        SideBySideEditorView.as_view(),
        name='editor'
    ),
    url(
        r'^editor/(?P<slug>[-\w]+)/(?P<path>.*)$',
        serve_attachment,
        name='serve_attachment'
    ),
    # we assume that there will be no task slugs consisting entirely of digits
    url(
        r'^(?P<id>[\d]+)/$',
        StaffSolutionDetailView.as_view(),
        name='staffdetail'
    ),
    url(
        r'^(?P<id>[\d]+)/status$',
        SolutionStatusView.as_view(),
        name='status'
    ),
    url(
        r'^(?P<solution_id>[\d]+)/archive/status$',
        SolutionArchiveStatusView.as_view(),
        name='archive_status'
    ),
    url(
        r'^(?P<solution_id>[\d]+)/archive/new$',
        NewSolutionArchiveView.as_view(),
        name='archive_new'
    ),
    url(
        r'^(?P<solution_id>[-\w]+)/archive/download$',
        SolutionArchiveDownloadView.as_view(),
        name='archive_download'
    ),
    url(
        r'^file/(?P<pk>[\d]+)/$',
        SolutionFileView.as_view(),
        name='showfile'
    ),
    url(
        r'^list/(?P<slug>[-\w]+)/$',
        SolutionListView.as_view(),
        name='list'
    ),
    url(
        r'^(?P<slug>[-\w]+)/detail/(?P<scoped_id>[\d]+)/$',
        SolutionDetailView.as_view(),
        name='detail'
    ),
    url(
        r'^(?P<slug>[-\w]+)/upload$',
        SolutionUploadView.as_view(),
        name='upload'
    ),
    url(
        r'^(?P<slug>[-\w]+)/checkpoints/save/$',
        save_checkpoint,
        name='save-checkpoint'
    ),
    url(
        r'^(?P<slug>[-\w]+)/checkpoints/last/$',
        get_last_checkpoint,
        name='get-last-checkpoint'
    ),
]
