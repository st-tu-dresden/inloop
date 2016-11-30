from django.conf.urls import url

from .views import current_site_response

urlpatterns = [
    url(r'^current_site_response/$', current_site_response),
]
