import logging

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from inloop.accounts import forms
from inloop.accounts.models import UserProfile

logger = logging.getLogger(__name__)


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


def register(request):
    if request.user.is_authenticated():
        return redirect('/')
    if request.method == 'POST':
        user_form = forms.UserForm(data=request.POST)
        if user_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password'])
            user.generate_activation_key()
            user.is_active = False
            user.save()
            try:
                user.send_activation_mail()
                return success(
                    request,
                    "Thanks for signing up. Your activation mail has been sent."
                )
            except Exception as e:
                logger.error("Could not send activation mail, stack trace follows.")
                logger.exception(e)
                return failure(request, "We are having trouble sending your activation mail.")
    else:
        user_form = forms.UserForm()

    return render(request, 'registration/register.html', {
        'user_form': user_form
    })


def activate_user(request, key):
    user = get_object_or_404(UserProfile, activation_key=key)
    if user.activate():
        return success(request, "Your account has been activated! You can now login.")
    else:
        return failure(request, "Your activation key has expired. Please register again.")


def user_login(request):
    if request.user.is_authenticated():
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


@login_required
def user_profile(request):
    if request.method == 'POST':
        user_profile = forms.UserProfileForm(
            data=request.POST,
            instance=request.user
        )
        if user_profile.is_valid():
            user_profile.save()
            return success(request, "Your profile information has successfully been changed.")
    else:
        user_profile = forms.UserProfileForm(
            instance=request.user,
            initial={'course': request.user.course, 'mat_num': request.user.mat_num}
        )

    return render(request, 'accounts/profile.html', {
        'user_profile': user_profile
    })


@login_required
def change_password(request):
    if request.method == 'POST':
        password_form = forms.PasswordForm(
            data=request.POST,
            instance=request.user
        )

        if password_form.is_valid():
            request.user.set_password(password_form.cleaned_data['password'])
            request.user.save()
            return success(request, "Your password has been changed successfully.")
    else:
        password_form = forms.PasswordForm(instance=request.user)

    return render(request, 'accounts/change_password.html', {
        'password_form': password_form
    })
