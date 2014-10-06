from django.conf.urls import patterns, url

#from accounts import views

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'prktmt.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^$', 'django.contrib.auth.views.login', name='login'),
    url(r'^login/$', 'django.contrib.auth.views.logout', name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.login', name='logout'),
)
