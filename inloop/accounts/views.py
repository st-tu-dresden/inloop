from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


def success(request, message):
    """Shortcut for displaying a success message to the user."""
    return render(request, "accounts/message.html", {
        "type": "success",
        "message": message
    })


def failure(request, message):
    """Shortcut for displaying a failure message to the user."""
    return render(request, "accounts/message.html", {
        "type": "danger",
        "message": message
    })


def user_login(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        # returns user object if credentials are valid
        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request, user)
                return redirect(settings.LOGIN_REDIRECT_URL)
            else:
                return failure(request, "Login not possible, your account is disabled.")
        else:
            return render(request, 'registration/login.html', {
                'login_failed': True
            })
    else:
        return render(request, 'registration/login.html')


@login_required
def user_logout(request):
    logout(request)
    return success(request, "You have been logged out. Bye!")
