from django.contrib.auth.decorators import user_passes_test


def superuser_required(function=None, redirect_field_name=None, login_url=None):
    """
    Decorator for views that checks if a user has superuser privileges
    and redirects to the log-in page if necessary.
    """
    # inspired by the code of Django's login_required:
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_superuser,
        login_url=None,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
