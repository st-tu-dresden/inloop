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

    url(r'^recover/(?P<signature>.+)/$', views.recover_done, name="recover_done"),
    url(r'^recover/$', views.recover, name="recover"),
    url(r'^reset/done/$', views.reset_done, name="reset_done"),
    url(r'^reset/(?P<token>[\w:-]+)/$', views.reset, name="reset"),
]
