import warnings
warnings.simplefilter("always")

from inloop.settings import *   # noqa

HUEY = {
    "always_eager": True,
}

PASSWORD_HASHERS = [
    # speed up tests involving user authentication
    "django.contrib.auth.hashers.SHA1PasswordHasher",
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
