from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^$', 'django.contrib.auth.views.login', name='login'),
    url(r'^login/$', 'django.contrib.auth.views.logout', name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.login', name='logout'),
)
