from django.contrib import admin
from django.contrib.flatpages.views import flatpage
from django.urls import include, path, re_path

from inloop.accounts import urls as account_urls
from inloop.gitload import urls as gitload_urls
from inloop.solutions import urls as solution_urls
from inloop.statistics import urls as statistics_urls
from inloop.tasks import urls as task_urls
from inloop.views import home, login, logout

urlpatterns = [
    path("", home, name="home"),
    path("login/", login, name="login"),
    path("logout/", logout, name="logout"),
    path("account/", include(account_urls)),
    path("gitload/", include(gitload_urls)),
    path("solutions/", include(solution_urls)),
    path("tasks/", include(task_urls)),
    path("statistics/", include(statistics_urls)),
    # explicitly override the admin logout url
    path("admin/logout/", logout),
    path("admin/", admin.site.urls),
]

# flatpages catchall pattern
urlpatterns += [
    re_path(r"^(?P<url>.*/)$", flatpage),
]

# customized titles and headers for the generated admin site
admin.site.site_header = "INLOOP administration"
admin.site.site_title = "INLOOP"
admin.site.index_title = "Manage accounts, tasks and solutions"
