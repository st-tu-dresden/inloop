from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.flatpages.views import flatpage

from inloop.accounts import urls as account_urls
from inloop.gh_import import urls as github_urls
from inloop.solutions import urls as solution_urls
from inloop.tasks import urls as task_urls
from inloop.tasks.views import index

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^solutions/', include(solution_urls)),
    url(r'^tasks/', include(task_urls)),
    url(r'^accounts/', include(account_urls)),
    url(r'^github/', include(github_urls)),
    url(r'^admin/', admin.site.urls),
]

# flatpages catchall pattern
urlpatterns += [
    url(r'^(?P<url>.*/)$', flatpage),
]

# customized titles and headers for the generated admin site
admin.site.site_header = "INLOOP administration"
admin.site.site_title = "INLOOP"
admin.site.index_title = "Manage accounts, tasks and solutions"
