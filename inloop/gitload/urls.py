from django.urls import path

from inloop.gitload.views import webhook_handler

app_name = "gitload"
urlpatterns = [
    path("webhook_handler/", webhook_handler, name="webhook_handler"),
]
