from django.conf.urls import url

import inloop.statistics.views as views

app_name = 'statistics'
urlpatterns = [
    url(
        r'^solutions/histogram/submissions/api/$',
        views.SubmissionsHistogramJsonView.as_view(),
        name='submissions_histogram_api'
    ),
    url(
        r'^solutions/histogram/attempts/api/$',
        views.AttemptsHistogramJsonView.as_view(),
        name='attempts_histogram_api'
    ),
]
