import os

from inloop.core.utils import filter_uppercase_keys
from inloop.settings import base

globals().update(filter_uppercase_keys(vars(base)))

SECRET_KEY = os.environ['SECRET_KEY']
SITE_ID = os.environ['SITE_ID']

# No debug pages!
DEBUG = False
TEMPLATE_DEBUG = DEBUG

# XXX: use contrib.sites for this, because contrib.auth does it too
DOMAIN = 'https://inloop.inf.tu-dresden.de/'

# Postgres connection parameters
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ['PG_NAME'],
        'USER': os.environ['PG_USER'],
        'PASSWORD': os.environ['PG_PASSWORD'],
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

# Email From: addresses
DEFAULT_FROM_EMAIL = 'no-reply@inloop.inf.tu-dresden.de'
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Send error reports to root (which is normally forwarded to
# a real address)
ADMINS = (('root', 'root@localhost'),)

# SMTP server settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25

# Use this if you are sure that your proxy (e.g., nginx) is always
# terminating SSL.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
