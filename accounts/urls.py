from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views

urlpatterns = patterns('',
    url(r'^$', auth_views.login, {'template_name': 'registration/login.html'}, name='auth_login'),
    url(r'^login/$', auth_views.login, {'template_name': 'registration/login.html'}, name='auth_login'),
    url(r'^logout/$', auth_views.logout_then_login, name='auth_logout'),
)
