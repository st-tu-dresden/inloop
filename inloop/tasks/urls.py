from django.urls import path, re_path
from django.views.generic.base import RedirectView

from inloop.tasks.views import TaskDetailView, category, index, serve_attachment

app_name = "tasks"
urlpatterns = [
    path("", index, name="index"),
    path("category/<slug:slug>/", category, name="category"),
    re_path(r"^detail/(?P<slug_or_name>[-\w]+)/$", TaskDetailView.as_view(), name="detail"),
    path("detail/<slug:slug>/<path:path>", serve_attachment, name="serve_attachment"),
    re_path(
        r"^(?P<slug_or_name>[-\w]+)/$",
        RedirectView.as_view(pattern_name="solutions:editor"),
        name="redirect-to-editor",
    ),
]
