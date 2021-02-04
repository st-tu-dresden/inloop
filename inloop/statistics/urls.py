from django.urls import path

import inloop.statistics.views as views

app_name = "statistics"
urlpatterns = [
    path("", views.StatisticsIndexTemplateView.as_view(), name="index"),
    path(
        "solutions/histogram/submissions/template/",
        views.SubmissionsHistogramTemplateView.as_view(),
        name="submissions_histogram",
    ),
    path(
        "solutions/histogram/submissions/api/",
        views.SubmissionsHistogramJsonView.as_view(),
        name="submissions_histogram_api",
    ),
    path(
        "solutions/histogram/attempts/template/",
        views.AttemptsHistogramTemplateView.as_view(),
        name="attempts_histogram",
    ),
    path(
        "solutions/histogram/attempts/api/",
        views.AttemptsHistogramJsonView.as_view(),
        name="attempts_histogram_api",
    ),
]
