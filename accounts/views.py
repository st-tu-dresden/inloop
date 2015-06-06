from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from . import forms
from .models import UserProfile


def new_course(request):
    if request.method == 'POST':
        course_form = forms.NewCourseForm(data=request.POST)
        if course_form.is_valid():
            course_form.save()
            return render(request, 'accounts/message.html', {
                'type': 'success',
                'message': 'The course has successfully been added!'
            })
        # XXX: else?
    else:
        course_form = forms.NewCourseForm()

    return render(request, 'accounts/new_course.html', {
        'course_form': course_form
    })


def register(request):
    if request.method == 'POST':
        user_form = forms.UserForm(data=request.POST)

        if user_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user.password)
            user.generate_activation_key()
            user.is_active = False
            user.save()
            user.send_activation_mail()
            return render(request, 'accounts/message.html', {
                'type': 'success',
                'message': 'Your activation mail has been sent!'
            })
        # XXX: else?

    else:
        user_form = forms.UserForm()

    return render(request, 'registration/register.html', {
        'user_form': user_form
    })


def activate_user(request, key):
    user = get_object_or_404(UserProfile, activation_key=key)
    user.activate()
    user.save()

    return render(request, 'accounts/message.html', {
        'type': 'success',
        'message': 'Your account has been activated! You can now login.'
    })


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        # returns user object if credentials are valid
        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                # everything alright
                login(request, user)
                return redirect('tasks:index')
            else:
                # account disabled
                return render(request, 'accounts/message.html', {
                    'type': 'danger',
                    'message': 'Your account is disabled!'
                })
        else:
            # invalid credentials
            return render(request, 'registration/login.html', {
                'login_failed': True
            })
    else:
        return render(request, 'registration/login.html')


@login_required(login_url='accounts/login/')
def user_logout(request):
    logout(request)
    return render(request, 'accounts/message.html', {
        'type': 'success',
        'message': 'You have been logged out!'
    })


@login_required(login_url='/accounts/login/')
def user_profile(request):
    if request.method == 'POST':
        user_profile = forms.UserProfileForm(
            data=request.POST,
            instance=request.user)
        if user_profile.is_valid():
            user_profile.save()
            return render(request, 'accounts/message.html', {
                'type': 'success',
                'message': 'Your profile information has successfully \
                been changed!'
            })
    else:
        user_profile = forms.UserProfileForm(
            instance=request.user,
            initial={
                'course': request.user.course,
                'mat_num': request.user.mat_num
            })

    return render(request, 'accounts/profile.html', {
        'user_profile': user_profile
    })
