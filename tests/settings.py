import warnings

warnings.simplefilter("always")

from inloop.settings import *   # noqa isort:skip

HUEY = {
    "always_eager": True,
}

PASSWORD_HASHERS = [
    # speed up tests involving user authentication
    "django.contrib.auth.hashers.SHA1PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = []

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

INSTALLED_APPS += [     # noqa
    "tests.unit.context_processors",
]

CONSTANCE_BACKEND = "tests.backends.ConstanceDictBackend"
