from os import path

from inloop.core.utils import filter_uppercase_keys
from inloop.settings import base

globals().update(filter_uppercase_keys(vars(base)))

local_conf = {}
with open("local_conf.py") as f:
    exec(f.read(), local_conf)

SITE_ID = 1
SECRET_KEY = local_conf['secret_key']
DOMAIN = 'https://{server_name}/'.format(**local_conf)

# No debug pages!
DEBUG = False

# Postgres connection parameters
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': local_conf['pg_name'],
        'USER': local_conf['pg_user'],
        'PASSWORD': local_conf['pg_pass'],
        'HOST': local_conf['pg_host'],
        'PORT': local_conf['pg_port'],
    }
}

# Path where `manage.py collectstatic` collects files
STATIC_ROOT = local_conf['static_root']

# Enable cache busting through hashed file names
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Path to media files
MEDIA_ROOT = local_conf['media_root']

# Security related settings
ALLOWED_HOSTS = [local_conf['server_name']]
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Email From: addresses
DEFAULT_FROM_EMAIL = 'no-reply@{server_name}'.format(**local_conf)
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Adresses to send error reports to (tuple of tuples (real name, email))
ADMINS = local_conf['admins']

# SMTP server settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25

# Use this if you are sure that your proxy (e.g., nginx) is always
# terminating SSL.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# The secret used for the webhook
GITHUB_SECRET = local_conf['github_secret']

# Settings related to the Git import
GIT_ROOT = path.join(MEDIA_ROOT, 'tasks')
GIT_SSH_KEY = None
GIT_SSH_URL = local_conf['tasks_repository']
GIT_BRANCH = local_conf['tasks_branch']

# Nginx X-Accel-Redirect support
SENDFILE_METHOD = "nginx"
SENDFILE_NGINX_URL = "/sendfile"

# Use sudo to run docker
base.CHECKER["USE_SUDO"] = True
