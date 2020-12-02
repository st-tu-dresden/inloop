from django.conf.urls import url

from inloop.accounts import views

app_name = "accounts"

urlpatterns = [
    url(r"^signup/$", views.signup, name="signup"),
    url(r"^signup/closed/$", views.signup_closed, name="signup_closed"),
    url(r"^signup/complete/$", views.signup_complete, name="signup_complete"),
    url(r"^activate/complete/$", views.activation_complete, name="activation_complete"),
    url(r"^activate/(?P<activation_key>[-:\w]+)/$", views.activate, name="activate"),
    url(r"^profile/$", views.profile, name="profile"),
    url(r"^password/$", views.password_change, name="password_change"),
    url(r"^confirm_ownwork/$", views.confirm_ownwork, name="confirm_ownwork"),
    url(r"^password_reset/$", views.password_reset, name="password_reset"),
    url(r"^password_reset_done/", views.password_reset_done, name="password_reset_done"),
    url(
        r"^password_reset_confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/"
        r"(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$",
        views.password_reset_confirm,
        name="password_reset_confirm",
    ),
    url(
        r"^password_reset_confirm_done/$",
        views.password_reset_complete,
        name="password_reset_complete",
    ),
]
