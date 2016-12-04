from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.views import login, logout
from django.contrib.flatpages.views import flatpage

from inloop.accounts import urls as account_urls
from inloop.gh_import import urls as github_urls
from inloop.solutions import urls as solution_urls
from inloop.tasks import urls as task_urls
from inloop.views import home

urlpatterns = [
    url(r'^$', home, name='home'),
    url(r'^login/$', login, name="login"),
    url(r'^logout/$', logout, name="logout"),

    url(r'^accounts/', include(account_urls)),
    url(r'^github/', include(github_urls)),
    url(r'^solutions/', include(solution_urls)),
    url(r'^tasks/', include(task_urls)),

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
