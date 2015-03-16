from django.conf.urls import patterns, url

from tasks import views

urlpatterns = patterns(
    '',
    url(r'^$', views.index, name='index'),
    url(r'^new_exercise/$', views.submit_new_exercise, name='new_exercise'),
    url(r'^(?P<slug>[-\w]+)/$', views.detail, name='detail'),
    url(r'^(?P<slug>\w+)/edit/$', views.edit, name='edit'),
    url(r'^(?P<slug>\w+)/results/$', views.results, name='results'),
    url(r'^(?P<slug>\w+)/delete/$', views.delete, name='delete'),
)
