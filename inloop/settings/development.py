"""
Quick start development settings which work out of the box -- UNSUITABLE for production.
"""
from os import environ
from os.path import dirname, join

from inloop.core.utils import filter_uppercase_keys
from inloop.settings import base

globals().update(filter_uppercase_keys(vars(base)))


SECRET_KEY = '8b)5ax&m^6ce8-id_0n%*5=rjsb-#(it91y9e0i_$p8o&2a#9a'
SITE_ID = 1

# XXX: Use contrib.sites for this
DOMAIN = 'http://localhost:8000/'

DEBUG = True

# Storage root for uploaded files
MEDIA_ROOT = join(base.PROJECT_ROOT, 'media')

# Debugging SMTP
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# SQLite is sufficient during development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': join(base.PROJECT_ROOT, 'db.sqlite3'),
    }
}

# The secret used for the webhook
GITHUB_SECRET = 'secret'

# Settings related to the Git import
GIT_SSH_KEY = None
GIT_SSH_URL = 'git@github.com:st-tu-dresden/inloop-tasks.git'
GIT_BRANCH = 'master'
GIT_ROOT = environ.get('GIT_ROOT', join(dirname(base.PROJECT_ROOT), 'inloop-tasks'))
