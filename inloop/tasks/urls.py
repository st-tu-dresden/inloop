from django.conf.urls import url

from inloop.tasks import views
from inloop.tasks.views import TaskDetailView

app_name = "tasks"
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^category/(?P<slug>[-\w]+)/$', views.category, name='category'),
    url(r'^(?P<slug>[-\w]+)/$', TaskDetailView.as_view(), name='detail'),
    url(r'^(?P<slug>[-\w]+)/(?P<path>.*)$', views.serve_attachment, name='serve_attachment'),
]
