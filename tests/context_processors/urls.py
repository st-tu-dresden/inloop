from django.urls import path

from .views import current_site_response

urlpatterns = [
    path("current_site_response/", current_site_response),
]
