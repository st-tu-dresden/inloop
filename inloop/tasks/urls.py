from django.conf.urls import patterns, url

from inloop.tasks import views

urlpatterns = patterns(
    '',
    url(
        r'^$',
        views.index,
        name='index'
    ),
    url(
        r'^category/(?P<short_id>[-\w]+)/$',
        views.category,
        name='category'
    ),
    url(
        r'^(?P<slug>[-\w]+)/$',
        views.detail,
        name='detail'
    ),
    url(
        r'^(?P<slug>[-\w]+)/results/(?P<solution_id>[\d]+)$',
        views.results,
        name='results'
    ),
    url(
        r'^(?P<slug>[-\w]+)/download_solution/(?P<solution_id>[\d]+)/$',
        views.get_solution_as_zip,
        name='solution_as_zip'
    ),
)
