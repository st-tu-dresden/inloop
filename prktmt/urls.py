from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'prktmt.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^tasks/', include('tasks.urls', namespace='tasks')),
    url(r'^accounts/', include('accounts.urls', namespace='accounts')),
    url(r'^admin/', include(admin.site.urls)),
)
