from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.flatpages import views as flatpage_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from inloop import views as sys_views
from inloop.accounts import urls as account_urls
from inloop.gh_import import urls as github_urls
from inloop.tasks import urls as task_urls
from inloop.tasks import views as task_views

urlpatterns = [
    url(r'^$', task_views.index, name='index'),
    url(r'^tasks/', include(task_urls, namespace='tasks')),
    url(r'^accounts/', include(account_urls, namespace='accounts')),
    url(r'^github/', include(github_urls, namespace='github')),
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

# customized titles and headers for the generated admin site
admin.site.site_header = "INLOOP administration"
admin.site.site_title = "INLOOP"
admin.site.index_title = "Manage accounts, tasks and solutions"
