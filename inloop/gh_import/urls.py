from django.conf.urls import patterns, url

from inloop.gh_import.views import PayloadView

urlpatterns = patterns(
    '',
    url(r'^payload$', PayloadView.as_view(), name='payload')
)
