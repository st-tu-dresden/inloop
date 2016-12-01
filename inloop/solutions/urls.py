from django.conf.urls import url

from inloop.solutions.views import (SolutionDetailView, SolutionListView,
                                    SolutionStatusView, SolutionUploadView)

app_name = "solutions"
urlpatterns = [
    url(r'^(?P<solution_id>[\d]+)/$', SolutionDetailView.as_view(), name='detail'),
    url(r'^(?P<solution_id>[\d]+)/status$', SolutionStatusView.as_view(), name='status'),
    url(r'^(?P<slug>[-\w]+)/$', SolutionListView.as_view(), name='list'),
    url(r'^(?P<slug>[-\w]+)/upload$', SolutionUploadView.as_view(), name='upload'),
]
