from django.conf.urls import patterns, url

from tasks import views

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'prktmt.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^$', views.index, name='index'),
    url(r'^task/(?P<slug>[-\w]+)/$', views.detail, name='detail'),
    url(r'^task/(?P<slug>\w+)/edit/$', views.edit, name='edit'),
    url(r'^task/(?P<slug>\w+)/results/$', views.results, name='results'),
)
