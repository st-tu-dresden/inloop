from django.conf.urls import url

from inloop.solutions.views import (ModalConfirmationView, ModalInputView, ModalNotificationView,
                                    ModularEditorTabView, SolutionDetailView,
                                    SolutionDownloadView, SolutionEditorView, SolutionFileView,
                                    SolutionListView, SolutionStatusView, SolutionUploadView,
                                    StaffSolutionDetailView)

app_name = "solutions"
urlpatterns = [
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
        r'^file/(?P<pk>[\d]+)/$',
        SolutionFileView.as_view(),
        name='showfile'
    ),
    url(
        r'^(?P<slug>[-\w]+)/$',
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
        r'^(?P<solution_id>[-\w]+)/download$',
        SolutionDownloadView.as_view(),
        name='download'
    ),
    url(
        r'^(?P<slug>[-\w]+)/editor$',
        SolutionEditorView.as_view(),
        name='editor'
    ),
    url(
        r'^(?P<slug>[-\w]+)/modular-editor-tab/$',
        ModularEditorTabView.as_view(),
        name='modular-tab'
    ),
    url(
        r'^(?P<slug>[-\w]+)/modal-notification/$',
        ModalNotificationView.as_view(),
        name='modal-notification'
    ),
    url(
        r'^(?P<slug>[-\w]+)/modal-input-form/$',
        ModalInputView.as_view(),
        name='modal-input-form'
    ),
    url(
        r'^(?P<slug>[-\w]+)/modal-confirmation-form/$',
        ModalConfirmationView.as_view(),
        name='modal-confirmation-form'
    ),
]
