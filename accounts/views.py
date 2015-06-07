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
    if user.activate():
        return render(request, 'accounts/message.html', {
            'type': 'success',
            'message': 'Your account has been activated! You can now login.'
        })
    else:
        return render(request, 'accounts/message.html', {
            'type': 'danger',
            'message': 'Your activation key has expired. \
            Please register again!'
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
                'message': 'Your profile information has \
                successfully been changed!'
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


@login_required
def change_email(request):
    user = UserProfile.objects.get(username=request.user.username)
    if request.method == 'POST':
        email_form = forms.EmailForm(data=request.POST)
        if request.POST['email'] != user.email and email_form.is_valid():
            user.generate_activation_key()
            user.send_mail_change_mail(request.POST['email'])
            return render(request, 'accounts/message.html', {
                'type': 'success',
                'message': 'A validation mail has been sent \
                to the new address!'
            })

    email_form = forms.EmailForm(initial={
        'email': user.email
    })

    return render(request, 'accounts/change_email.html', {
        'email_form': email_form
    })


def activate_email(request, key):
    user = get_object_or_404(UserProfile, activation_key=key)
    if user.activate_mail():
        return render(request, 'accounts/message.html', {
            'type': 'success',
            'message': 'Your email has successfully been changed!'
        })
    else:
        return render(request, 'accounts/message.html', {
            'type': 'danger',
            'message': 'Your key has expired. \
            Please try changing your email again!'
        })


@login_required
def change_password(request):
    if request.method == 'POST':
        password_form = forms.PasswordForm(
            data=request.POST,
            instance=request.user)

        if password_form.is_valid():
            return render(request, 'accounts/message.html', {
                'type': 'success',
                'message': 'A validation mail has been sent \
                to your email address!'
            })
    else:
        password_form = forms.PasswordForm(instance=request.user)

    return render(request, 'accounts/change_password.html', {
        'password_form': password_form
    })
