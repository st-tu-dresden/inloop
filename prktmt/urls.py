from django.conf.urls import patterns, include, url
from django.contrib import admin

# To serve static files during development!
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = patterns('',
    url(r'^tasks/', include('tasks.urls', namespace='tasks')),
    url(r'^accounts/', include('accounts.urls', namespace='accounts')),
    url(r'^admin/', include(admin.site.urls)),
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
