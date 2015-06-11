"""
Base settings for inloop project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

from os.path import dirname, join
from sys import version_info

if version_info[0] < 3:
    raise RuntimeError("INLOOP must be run with Python 3.x")

BASE_DIR = dirname(dirname(dirname(__file__)))

DEBUG = False
TEMPLATE_DEBUG = DEBUG

AUTH_USER_MODEL = 'accounts.UserProfile'

# Debugging SMTP
DOMAIN = 'http://localhost:8000/'

# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.flatpages',
    'accounts',
    'tasks',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
)

LOGIN_REDIRECT_URL = '/tasks'
ROOT_URLCONF = 'inloop.urls'
WSGI_APPLICATION = 'inloop.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = ''

# Storage location for uploaded files
MEDIA_ROOT = join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Static file search path
STATICFILES_DIRS = (
    join(BASE_DIR, 'static'),
)

# Template search paths
TEMPLATE_DIRS = (
    join(BASE_DIR, 'templates'),
    # otherwise django.contrib.auth won't find the custom templates
    join(BASE_DIR, 'accounts', 'templates')
)
