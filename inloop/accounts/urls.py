from django.conf.urls import patterns, url

import inloop.accounts.views as account_views

urlpatterns = patterns(
    '',
    url(
        r'^profile/$',
        account_views.user_profile,
        name='user_profile'
    ),
    url(
        r'^password_change/$',
        'django.contrib.auth.views.password_change',
        {'post_change_redirect': 'accounts:password_change_done'},
        name='password_change'
    ),
    url(
        r'^password_change_done/$',
        'django.contrib.auth.views.password_change_done',
        name='password_change_done'
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
        r'^activate/(?P<key>[0-9a-zA-Z]{40})$',
        account_views.activate_user,
        name='user_activation'
    ),
    url(
        r'^reset_password/$',
        'django.contrib.auth.views.password_reset',
        {'post_reset_redirect': '/accounts/reset_password/done/'},
        name='password_reset'
    ),
    url(
        r'^reset_password/done/$',
        'django.contrib.auth.views.password_reset_done',
        {'template_name': 'registration/password_reset_done.html'},
        name='password_reset_done'
    ),
    url(
        r'^reset_password/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
        'django.contrib.auth.views.password_reset_confirm',
        {
            'template_name': 'registration/password_reset_confirm.html',
            'post_reset_redirect': '/accounts/reset_password/complete/'
        },
        name='password_reset_confirm'
    ),
    url(
        r'^reset_password/complete/$',
        'django.contrib.auth.views.password_reset_complete',
        {'template_name': 'registration/password_reset_complete.html'},
        name='password_reset_complete'
    ),
)
