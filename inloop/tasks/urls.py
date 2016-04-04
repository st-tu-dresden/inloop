from django.conf.urls import url

from inloop.tasks import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^category/(?P<short_id>[-\w]+)/$', views.category, name='category'),
    url(r'^(?P<slug>[-\w]+)/$', views.detail, name='detail'),
    url(r'^(?P<slug>[-\w]+)/results/(?P<solution_id>[\d]+)$', views.results, name='results'),
    url(r'^(?P<slug>[-\w]+)/download_solution/(?P<solution_id>[\d]+)/$',
        views.get_solution_as_zip, name='solution_as_zip'),
    url(r'^(?P<slug>[-\w]+)/(?P<path>.*)$', views.serve_attachment, name='serve_attachment'),
]
