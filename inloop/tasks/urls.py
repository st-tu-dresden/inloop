from django.urls import path, re_path
from django.views.generic.base import RedirectView

from inloop.tasks.views import category, index

app_name = "tasks"
urlpatterns = [
    path("", index, name="index"),
    path("category/<slug:slug>/", category, name="category"),
    re_path(
        r"^(?P<slug_or_name>[-\w]+)/$",
        RedirectView.as_view(pattern_name="solutions:editor"),
        name="redirect-to-editor",
    ),
]
