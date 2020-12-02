from django.template.response import TemplateResponse


def current_site_response(request):
    return TemplateResponse(request, "context_processors/current_site.html")
