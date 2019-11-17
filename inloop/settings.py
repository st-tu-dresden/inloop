"""
INLOOP settings module, inspired by 12factor.

Configuration is entirely controlled by environment vars. See
docs/deployment.md for a list and description of available options.

"""

import sys
from collections import OrderedDict
from pathlib import Path

from django.contrib.messages import constants as messages
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse_lazy

from environ import Env

from inloop.accounts import constance as accounts_constance
from inloop.gitload import constance as gitload_constance
from inloop.solutions import constance as solutions_constance

if sys.getfilesystemencoding() != "utf-8":
    raise ImproperlyConfigured("LANG must be a utf-8 locale")

PACKAGE_DIR = Path(__file__).resolve().parent
BASE_DIR = PACKAGE_DIR.parent

env = Env()

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = [host.strip() for host in env.list("ALLOWED_HOSTS")]
INTERNAL_IPS = [ip.strip() for ip in env.list("INTERNAL_IPS", default="")]

SITE_ID = 1

INSTALLED_APPS = [
    "inloop.accounts",
    "inloop.common",
    "inloop.grading",
    "inloop.solutions",
    "inloop.tasks",
    "inloop.testrunner",
    "inloop.gitload",

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "django.contrib.flatpages",

    "constance",
    "django_extensions",
    "huey.contrib.djhuey",
    "widget_tweaks",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.auth.middleware.SessionAuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

LOGIN_REDIRECT_URL = reverse_lazy("home")
LOGIN_URL = reverse_lazy("home")

ROOT_URLCONF = "inloop.urls"
APPEND_SLASH = True
WSGI_APPLICATION = "inloop.wsgi.application"

if DEBUG and env.bool("DJDT", default=False):
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
    ROOT_URLCONF = "inloop.debug_urls"

if DEBUG and env.bool("HTMLVALIDATOR_ENABLED", default=False):
    HTMLVALIDATOR_VNU_PORT = env.str("HTMLVALIDATOR_VNU_PORT", default=None)
    if not HTMLVALIDATOR_VNU_PORT:
        raise ValueError(
            "The vnu validator is enabled, but no port was given. Please "
            "specify a port with the corresponding environment variable."
        )
    HTMLVALIDATOR_VNU_URL = "http://localhost:{}/".format(HTMLVALIDATOR_VNU_PORT)
    HTMLVALIDATOR_ENABLED = True
    HTMLVALIDATOR_OUTPUT = "stdout"
    MIDDLEWARE.append("htmlvalidator.middleware.HTMLValidator")

TIME_ZONE = env("TIME_ZONE", default="Europe/Berlin")
USE_TZ = True

USE_I18N = USE_L10N = False

FIRST_DAY_OF_WEEK = 1
TIME_FORMAT = "H:i"
DATE_FORMAT = "d-m-Y"
DATETIME_FORMAT = DATE_FORMAT + ", " + TIME_FORMAT
SHORT_DATE_FORMAT = DATE_FORMAT
SHORT_DATETIME_FORMAT = DATETIME_FORMAT

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [
        str(PACKAGE_DIR / "templates"),
    ],
    "OPTIONS": {
        "loaders": [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ],
        "context_processors": [
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
            "inloop.common.context_processors.current_site",
        ],
        "debug": DEBUG
    },
}]

if not DEBUG:
    TEMPLATES[0]["OPTIONS"]["loaders"] = [
        ("django.template.loaders.cached.Loader", TEMPLATES[0]["OPTIONS"]["loaders"]),
    ]

STATICFILES_DIRS = [str(BASE_DIR / "assets")]

# adapt the default message tags to Bootstrap CSS
MESSAGE_TAGS = {
    messages.DEBUG: "info",
    messages.ERROR: "danger",
}

DATABASES = {
    "default": env.db()
}

CACHES = {
    "default": env.cache()
}

# TODO: LOGGING = { ... }

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_COOKIE_AGE = 7 * 24 * 3600

STATIC_URL = env("STATIC_URL", default="/static/")
MEDIA_URL = env("MEDIA_URL", default="/media/")

if DEBUG:
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
    STATIC_ROOT = env("STATIC_ROOT", default=None)
    MEDIA_ROOT = str(BASE_DIR / "media")
else:
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
    STATIC_ROOT = env("STATIC_ROOT")
    MEDIA_ROOT = env("MEDIA_ROOT")

vars().update(env.email(default="smtp://:@localhost:25"))

ADMINS = [
    ("", email.strip()) for email in env.list("ADMINS")
]
EMAIL_SUBJECT_PREFIX = "[INLOOP] "
DEFAULT_FROM_EMAIL = SERVER_EMAIL = env("FROM_EMAIL")

if env.bool("PROXY_ENABLED", default=False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True
    MIDDLEWARE.insert(0, "inloop.common.middleware.SetRemoteAddrFromForwardedFor")
    X_ACCEL_LOCATION = env("X_ACCEL_LOCATION")

if env.bool("SECURE_COOKIES", default=True):
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# necessary to pass security audits:
CSRF_COOKIE_HTTPONLY = True

HUEY = {
    "always_eager": False,
    "url": env("REDIS_URL"),
}

TESTRUNNER_OPTIONS = {
    "timeout": 120,
}
TESTRUNNER_IMAGE = "inloop-testrunner"

REPOSITORY_ROOT = str(Path(MEDIA_ROOT) / "repository")

ACCOUNT_ACTIVATION_DAYS = 7

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    # NumericPasswordValidator skipped (see OWASP presentation https://youtu.be/zUM7i8fsf0g)
]

CONSTANCE_REDIS_CONNECTION = env("REDIS_URL")

CONSTANCE_CONFIG = OrderedDict()
CONSTANCE_CONFIG_FIELDSETS = {}
CONSTANCE_ADDITIONAL_FIELDS = {}

CONSTANCE_CONFIG.update(accounts_constance.config)
CONSTANCE_CONFIG_FIELDSETS.update(accounts_constance.fieldsets)
CONSTANCE_ADDITIONAL_FIELDS.update(accounts_constance.fields)

CONSTANCE_CONFIG.update(gitload_constance.config)
CONSTANCE_CONFIG_FIELDSETS.update(gitload_constance.fieldsets)

CONSTANCE_CONFIG.update(solutions_constance.config)
CONSTANCE_CONFIG_FIELDSETS.update(solutions_constance.fieldsets)

JPLAG_JAR_PATH = str(BASE_DIR / "lib" / "jplag-2.11.9-SNAPSHOT.jar")
JPLAG_SIMILARITY = 90
