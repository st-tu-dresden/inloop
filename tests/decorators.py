"""Decorators for test methods."""

from functools import wraps


def assert_login(username, password):
    """
    Decorator that adds an asserted login with the given credentials
    at the beginning of the decorated test method.

    Usage:
        @assert_login("bob", "secret")
        def test_xyz(self):
            # self.client is now logged in
            ...

    The decorated method must be in a subclass of django.test.TestCase.
    """
    def decorator(decorated_method):
        @wraps(decorated_method)
        def wrapper(self):
            if not self.client.login(username=username, password=password):
                raise AssertionError("Could not login with %s" % {'username': username,
                                                                  'password': password})
            return decorated_method(self)
        return wrapper
    return decorator
