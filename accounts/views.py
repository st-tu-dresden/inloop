from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from accounts.forms import UserForm, NewCourseForm


def new_course(request):
    if request.method == 'POST':
        course_form = NewCourseForm(data=request.POST)
        if course_form.is_valid():
            course_form.save()
            return render(request, 'accounts/message.html', {
                'type': 'success',
                'message': 'The course has successfully been added!'
            })
        else:
            error_msg = "The following form validation errors occurred: {0}"
            print(error_msg.format(course_form.errors))
    else:
        course_form = NewCourseForm()

    return render(request, 'accounts/new_course.html', {
        'course_form': course_form
    })


def register(request):
    if request.method == 'POST':
        user_form = UserForm(data=request.POST)

        if user_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()
            return render(request, 'accounts/message.html', {
                'type': 'success',
                'message': 'You have successfully been registered!'
            })
        else:
            error_msg = "The following form validation errors occurred: {0}"
            print(error_msg.format(user_form.errors))

    else:
        user_form = UserForm()

    return render(request, 'registration/register.html', {
        'user_form': user_form
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
                    'message': 'Your account has been disabled!'
                })
        else:
            # invalid credentials
            print('Invalid login details: {0}, {1}'.format(username, password))
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
    pass
