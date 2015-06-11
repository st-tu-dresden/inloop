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
        r'^profile/$',
        account_views.user_profile,
        name='user_profile'
    ),
    url(
        r'^change_email/$',
        account_views.change_email,
        name='change_email'
    ),
    url(
        r'^change_password/$',
        account_views.change_password,
        name='change_password'
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
    ),
    url(
        r'activate_mail/(?P<key>[0-9a-f]{5,40})$',
        account_views.activate_email,
        name='activate_email'
    ),
    url(
        r'^reset_password/$',
        'django.contrib.auth.views.password_reset',
        {'post_reset_redirect': 'done/'},
        name='password_reset'
    ),
    url(
        r'^reset_password/done/$',
        'django.contrib.auth.views.password_reset_done',
        {'template_name': 'registration/password_reset_done.html'},
        name='password_reset_done'
    ),
    url(
        r'^reset_password/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
        'django.contrib.auth.views.password_reset_confirm',
        {
            'template_name': 'password_reset_confirm.html',
            'post_reset_redirect': 'complete/'
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
