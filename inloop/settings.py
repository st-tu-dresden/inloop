"""
INLOOP settings module, inspired by 12factor.

Configuration is entirely controlled by environment vars. See docs/deployment-guide.md
for a list and description of available options.
"""
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse_lazy
from environ import Env
from redis.connection import ConnectionPool

if sys.getfilesystemencoding() != "utf-8":
    raise ImproperlyConfigured("LANG must be a utf-8 locale")

PACKAGE_DIR = Path(__file__).resolve().parent
BASE_DIR = PACKAGE_DIR.parent
INLOOP_ROOT = str(PACKAGE_DIR)  # XXX: deprecated in favor of PACKAGE_DIR

env = Env()

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = [host.strip() for host in env.list("ALLOWED_HOSTS")]

SITE_ID = 1
DOMAIN = env("SERVER_NAME", default="localhost:8000")   # XXX: use contrib.sites

AUTH_USER_MODEL = "accounts.UserProfile"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "django.contrib.flatpages",

    "django_extensions",
    "huey.contrib.djhuey",

    "inloop.core",
    "inloop.accounts",
    "inloop.tasks",
    "inloop.gh_import",
]

if DEBUG and env.bool("DJDT", default=False):
    INSTALLED_APPS.append("debug_toolbar")
    DEBUG_TOOLBAR_CONFIG = {"JQUERY_URL": ""}

MIDDLEWARE_CLASSES = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.auth.middleware.SessionAuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

LOGIN_REDIRECT_URL = reverse_lazy("index")
LOGIN_URL = reverse_lazy("index")

ROOT_URLCONF = "inloop.urls"
WSGI_APPLICATION = "inloop.wsgi.application"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_L10N = True
USE_TZ = True
FIRST_DAY_OF_WEEK = 1

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [
        str(PACKAGE_DIR / "templates"),
        str(PACKAGE_DIR / "accounts" / "templates"),
    ],
    "APP_DIRS": True,
    "OPTIONS": {
        "context_processors": [
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
        ],
    },
}]

# TODO: investigate a better method to align Bootstrap alerts and contrib.messages
MESSAGE_TAGS = {10: "info", 40: "danger"}

DATABASES = {
    "default": env.db()
}

CACHES = {
    "default": env.cache()
}

# TODO: LOGGING = { ... }

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_COOKIE_AGE = 7 * 24 * 3600

if not DEBUG:
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
STATIC_URL = env("STATIC_URL", default="/static/")
STATIC_ROOT = env("STATIC_ROOT", default=str(BASE_DIR / "static"))

MEDIA_URL = env("MEDIA_URL", default="/media/")
MEDIA_ROOT = env("MEDIA_ROOT", default=str(BASE_DIR / "media"))

if env.bool("SECURE_COOKIES", default=False):
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

vars().update(env.email(default="smtp://:@localhost:25"))

ADMINS = [
    ("", email.strip()) for email in env.list("ADMINS", default="")
]
EMAIL_SUBJECT_PREFIX = "[INLOOP] "
DEFAULT_FROM_EMAIL = SERVER_EMAIL = env("FROM_EMAIL")

if env.bool("USE_X_FORWARDED", default=False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True

HUEY = {
    "always_eager": False,
    "connection_pool": ConnectionPool.from_url(env("REDIS_URL")),
}

SENDFILE_METHOD = "django"
if env("SENDFILE_NGINX_URL", default=None):
    SENDFILE_METHOD = "nginx"
    SENDFILE_NGINX_URL = env("SENDFILE_NGINX_URL")

CHECKER = {
    "timeout": 120,
}
DOCKER_IMAGE = "inloop-java-checker"

GITHUB_SECRET = env("GITHUB_SECRET")
GIT_ROOT = str(Path(MEDIA_ROOT) / "tasks")
GIT_SSH_URL = env("GIT_URL", default="")
GIT_SSH_KEY = None
GIT_BRANCH = env("GIT_BRANCH", default="master")
