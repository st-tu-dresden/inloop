import warnings

warnings.simplefilter("always")

# pylint: disable=wildcard-import,unused-wildcard-import
from inloop.settings import *   # noqa isort:skip

HUEY = {
    "always_eager": True,
}

PASSWORD_HASHERS = [
    # speed up tests involving user authentication
    "django.contrib.auth.hashers.SHA1PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = []

CONSTANCE_BACKEND = "tests.backends.ConstanceDictBackend"

INSTALLED_APPS += [     # noqa
    "tests.unit.context_processors",
]
