from django.conf.urls import url

from inloop.accounts import views

app_name = "accounts"

urlpatterns = [
    url(r'^signup/$', views.signup, name="signup"),
    url(r'^signup/closed/$', views.signup_closed, name="signup_closed"),
    url(r'^signup/complete/$', views.signup_complete, name="signup_complete"),
    url(r'^activate/complete/$', views.activation_complete, name="activation_complete"),
    url(r'^activate/(?P<activation_key>[-:\w]+)/$', views.activate, name="activate"),
    url(r'^profile/$', views.profile, name="profile"),
    url(r'^password/$', views.password_change, name="password_change"),
]
