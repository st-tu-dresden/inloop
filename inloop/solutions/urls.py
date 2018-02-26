from django.conf.urls import url

from inloop.solutions.views import (SolutionDetailView, SolutionListView, SolutionStatusView,
                                    SolutionUploadView, StaffSolutionDetailView)

app_name = "solutions"
urlpatterns = [
    # we assume that there will be no task slugs consisting entirely of digits
    url(r'^(?P<id>[\d]+)/$', StaffSolutionDetailView.as_view(), name='staffdetail'),
    url(r'^(?P<id>[\d]+)/status$', SolutionStatusView.as_view(), name='status'),
    url(r'^(?P<slug>[-\w]+)/$', SolutionListView.as_view(), name='list'),
    url(r'^(?P<slug>[-\w]+)/(?P<scoped_id>[\d]+)/$', SolutionDetailView.as_view(), name='detail'),
    url(r'^(?P<slug>[-\w]+)/upload$', SolutionUploadView.as_view(), name='upload'),
]
