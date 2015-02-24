from django.conf.urls import patterns, include, url
from django.contrib import admin

# To serve static files during development
from django.conf import settings
from django.conf.urls.static import static

from tasks import views as task_views

urlpatterns = patterns(
    '',
    url(r'^$', task_views.index, name='index'),
    url(r'^tasks/', include('tasks.urls', namespace='tasks')),
    url(r'^accounts/', include('accounts.urls', namespace='accounts')),
    url(r'^admin/', include(admin.site.urls)),
)
# serve static content
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# flatpages catchall pattern
urlpatterns += patterns(
    'django.contrib.flatpages.views',
    (r'^(?P<url>.*/)$', 'flatpage'),
)
