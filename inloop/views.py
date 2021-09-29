from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.views import LoginView
from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed, HttpResponseRedirect
from django.urls import reverse
from django.views.csrf import csrf_failure as django_csrf_failure
from django.views.decorators.cache import never_cache

from inloop.tasks.views import index as task_index

login = LoginView.as_view(extra_context={"hide_login_link": True})


def home(request: HttpRequest) -> HttpResponse:
    if request.user.is_anonymous:
        return login(request)
    return task_index(request)


@never_cache
def logout(request: HttpRequest) -> HttpResponse:
    """Logout the user, allowing HTTP POST only."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"], "Logout only possible via POST.")
    auth_logout(request)
    messages.success(request, "You have been logged out. We hope to see you soon again!")
    return HttpResponseRedirect(reverse("home"))


# custom CSRF failure view that ensures proper no-cache headers
csrf_failure = never_cache(django_csrf_failure)
