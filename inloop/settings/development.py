from os import path

from .base import *
from . import base

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

SECRET_KEY = '8b)5ax&m^6ce8-id_0n%*5=rjsb-#(it91y9e0i_$p8o&2a#9a'
SITE_ID = 1

# XXX: Use contrib.sites for this
DOMAIN = 'http://localhost:8000/'

DEBUG = True
TEMPLATE_DEBUG = DEBUG

# Storage root for uploaded files
MEDIA_ROOT = path.join(base.BASE_DIR, 'media')

# Debugging SMTP
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# SQLite is sufficient during development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': path.join(base.BASE_DIR, 'db.sqlite3'),
    }
}
