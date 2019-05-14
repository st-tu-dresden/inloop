from functools import wraps


def assert_login(username, password):
    """
    Supply a decorator that verifies successful
    login before any subsequent test operations.
    """
    def inner(method):
        @wraps(inner)
        def wrapper(test):
            test.assertTrue(test.client.login(username=username, password=password))
            method(test)
        return wrapper
    return inner
