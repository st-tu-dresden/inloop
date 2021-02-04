from django.urls import path, re_path

from inloop.accounts import views

app_name = "accounts"

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("signup/closed/", views.signup_closed, name="signup_closed"),
    path("signup/complete/", views.signup_complete, name="signup_complete"),
    path("activate/complete/", views.activation_complete, name="activation_complete"),
    re_path(r"^activate/(?P<activation_key>[-:\w]+)/$", views.activate, name="activate"),
    path("profile/", views.profile, name="profile"),
    path("password/", views.password_change, name="password_change"),
    path("confirm_ownwork/", views.confirm_ownwork, name="confirm_ownwork"),
    path("password_reset/", views.password_reset, name="password_reset"),
    path("password_reset_done/", views.password_reset_done, name="password_reset_done"),
    path(
        "password_reset_confirm/<uidb64>/<token>/",
        views.password_reset_confirm,
        name="password_reset_confirm",
    ),
    path(
        "password_reset_confirm_done/",
        views.password_reset_complete,
        name="password_reset_complete",
    ),
]
