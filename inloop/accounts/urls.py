from django.conf.urls import url

from inloop.accounts import views

app_name = "accounts"

urlpatterns = [
    url(r'^activate/$', views.activate, name="activate"),
    url(r'^create/$', views.register, name="register"),
    url(r'^profile/$', views.profile, name="profile"),
    url(r'^password/$', views.password_change, name="password_change"),
]
