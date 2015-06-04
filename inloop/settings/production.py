from os import environ as env

from .base import *

SECRET_KEY = env['SECRET_KEY']
SITE_ID = env['SITE_ID']

# No debug pages!
DEBUG = False
TEMPLATE_DEBUG = DEBUG

# Postgres connection parameters
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': env['PG_NAME'],
        'USER': env['PG_USER'],
        'PASSWORD': env['PG_PASSWORD'],
        # HOST and PORT are omitted, defaults to using unix sockets
    }
}

# Path where `manage.py collectstatic` collects files
STATIC_ROOT = '/srv/inloop.inf.tu-dresden.de/static'

# Path to media files
MEDIA_ROOT = '/srv/inloop.inf.tu-dresden.de/media'

# Security related settings
ALLOWED_HOSTS = ['inloop.inf.tu-dresden.de']
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# SMTP server settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25

# Use this if you are sure that your proxy (e.g., nginx) is always
# terminating SSL.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
