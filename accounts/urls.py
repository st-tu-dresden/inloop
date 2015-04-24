from django.conf.urls import patterns, url
import accounts.views as account_views

urlpatterns = patterns(
    '',
    url(
        r'^new_course/$',
        account_views.new_course,
        name='new_course'
    ),
    url(
        r'^register/$',
        account_views.register,
        name='register'
    ),
    url(
        r'^login/$',
        account_views.user_login,
        name='user_login'
    ),
    url(
        r'^logout/$',
        account_views.user_logout,
        name='user_logout'
    ),
    url(
        r'^activate/(?P<key>[0-9a-f]{5,40})$',
        account_views.activate_user,
        name='user_activation'
    )
)
