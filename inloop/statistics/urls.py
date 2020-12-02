from django.conf.urls import url

import inloop.statistics.views as views

app_name = "statistics"
urlpatterns = [
    url(r"^$", views.StatisticsIndexTemplateView.as_view(), name="index"),
    url(
        r"^solutions/histogram/submissions/template/$",
        views.SubmissionsHistogramTemplateView.as_view(),
        name="submissions_histogram",
    ),
    url(
        r"^solutions/histogram/submissions/api/$",
        views.SubmissionsHistogramJsonView.as_view(),
        name="submissions_histogram_api",
    ),
    url(
        r"^solutions/histogram/attempts/template/$",
        views.AttemptsHistogramTemplateView.as_view(),
        name="attempts_histogram",
    ),
    url(
        r"^solutions/histogram/attempts/api/$",
        views.AttemptsHistogramJsonView.as_view(),
        name="attempts_histogram_api",
    ),
]
