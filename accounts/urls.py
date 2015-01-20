from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
import accounts.views as account_views

urlpatterns = patterns('',
                       url(r'^register/$', account_views.register, name='register'),
                       url(r'^login/$', account_views.user_login, name='user_login'),
                       url(r'^logout/$', auth_views.logout_then_login,
                           {'template_name': 'registration/logged_out.html'}, name='auth_logout'),
)