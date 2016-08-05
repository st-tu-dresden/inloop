from django.conf.urls import url

from inloop.tasks import views
from inloop.tasks.views import (SolutionDetailView, SolutionListView,
                                SolutionStatusView,
                                SolutionUploadView, TaskDetailView)

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^category/(?P<slug>[-\w]+)/$', views.category, name='category'),
    url(r'^solution/(?P<solution_id>[\d]+)/$',
        SolutionDetailView.as_view(), name='solutiondetail'),
    url(r'^solution/(?P<solution_id>[\d]+)/status$',
        SolutionStatusView.as_view(), name='solutionstatus'),
    url(r'^(?P<slug>[-\w]+)/$', TaskDetailView.as_view(), name='detail'),
    url(r'^(?P<slug>[-\w]+)/upload$', SolutionUploadView.as_view(), name='solutionupload'),
    url(r'^(?P<slug>[-\w]+)/solutions$', SolutionListView.as_view(), name='solutionlist'),
    url(r'^(?P<slug>[-\w]+)/(?P<path>.*)$', views.serve_attachment, name='serve_attachment'),
]
