from django.conf.urls import url

from inloop.gh_import.views import PayloadView

app_name = "github"
urlpatterns = [
    url(r'^payload$', PayloadView.as_view(), name='payload')
]
