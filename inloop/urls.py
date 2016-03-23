from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.flatpages import views as flatpage_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from inloop import views as sys_views
from inloop.tasks import views as task_views

urlpatterns = [
    url(r'^$', task_views.index, name='index'),
    url(r'^tasks/', include('inloop.tasks.urls', namespace='tasks')),
    url(r'^accounts/', include('inloop.accounts.urls', namespace='accounts')),
    url(r'^github/', include('inloop.gh_import.urls', namespace='github')),
    url(r'^admin/', include(admin.site.urls)),
]

# serve static content
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# add error pages for testing
if settings.DEBUG:
    urlpatterns += [
        url(r'^404$', sys_views.handler404),
        url(r'^500$', sys_views.handler500),
        url(r'^trigger_error$', sys_views.trigger_error),
    ]

# flatpages catchall pattern
urlpatterns += [
    url(r'^(?P<url>.*/)$', flatpage_views.flatpage),
]
