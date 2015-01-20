from django.conf.urls import patterns, include, url
from django.contrib import admin

# To serve static files during development
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = patterns('',
                       url(r'^$', include('tasks.urls', namespace='tasks')),
                       url(r'^pages/', include('django.contrib.flatpages.urls')),
                       url(r'^tasks/', include('tasks.urls', namespace='tasks')),
                       url(r'^accounts/', include('accounts.urls', namespace='accounts')),
                       url(r'^admin/', include(admin.site.urls)),
)
# serve static content
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# regular flatpages
urlpatterns += patterns('django.contrib.flatpages.views',
                        url(r'^index/$', 'flatpage', {'url': '/index/'}, name='index'),
                        url(r'^about/$', 'flatpage', {'url': '/about/'}, name='about'),
                        url(r'^legal/$', 'flatpage', {'url': '/legal/'}, name='legal'),
)

# flatpages catchall pattern
urlpatterns += patterns('django.contrib.flatpages.views',
                        (r'^(?P<url>.*/)$', 'flatpage'),
)
