from django.conf.urls import url

from inloop.gitload.views import webhook_handler

app_name = "gitload"
urlpatterns = [url(r"^webhook_handler/$", webhook_handler, name="webhook_handler")]
