from django.conf.urls import url

from inloop.tasks import views
from inloop.tasks.views_new import SolutionStatusView

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^category/(?P<slug>[-\w]+)/$', views.category, name='category'),
    url(r'^solution/(?P<solution_id>[\d]+)/status$',
        SolutionStatusView.as_view(), name='solutionstatus'),
    url(r'^(?P<slug>[-\w]+)/$', views.detail, name='detail'),
    url(r'^(?P<slug>[-\w]+)/results/(?P<solution_id>[\d]+)$', views.results, name='results'),
    url(r'^(?P<slug>[-\w]+)/download_solution/(?P<solution_id>[\d]+)/$',
        views.get_solution_as_zip, name='solution_as_zip'),
    url(r'^(?P<slug>[-\w]+)/(?P<path>.*)$', views.serve_attachment, name='serve_attachment'),
]
