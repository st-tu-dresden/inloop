from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import ObjectDoesNotExist, Q
from django.http import Http404, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.generic import View

from inloop.tasks.models import Task


class SideBySideEditorView(LoginRequiredMixin, View):
    """
    Show the task description referenced by slug or system_name.

    Requests with a non-slug url are redirected to their slug url equivalent.
    """

    def get(self, request, slug_or_name):
        qs = Task.objects.published()
        try:
            task = qs.filter(Q(slug=slug_or_name) | Q(system_name=slug_or_name)).get()
        except ObjectDoesNotExist:
            raise Http404

        if slug_or_name != task.slug:
            return HttpResponseRedirect(reverse('tasks:detail', args=[task.slug]))

        return TemplateResponse(request, 'solutions/editor-v2.html', {'task': task})
