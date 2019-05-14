from functools import wraps

from django.contrib.auth.models import User


def assert_login(username, password):
    """
    Supply a decorator that verifies successful
    login before any subsequent test operations.
    """
    def inner(method):
        @wraps(inner)
        def wrapper(test):
            if not User.objects.filter(username=username).exists():
                test.fail("There is no user with the username: {}".format(username))
            test.assertTrue(
                test.client.login(username=username, password=password),
                "Login failed for the given username and password: ({}, {})".format(
                    username, password
                )
            )
            method(test)
        return wrapper
    return inner
