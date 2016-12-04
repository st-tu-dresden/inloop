from django.template.response import TemplateResponse

from inloop.tasks.views import index as task_index


def home(request):
    if request.user.is_anonymous:
        return TemplateResponse(request, "registration/login.html", {"hide_login_link": True})
    return task_index(request)
