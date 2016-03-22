from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.crypto import constant_time_compare
from django.utils.decorators import method_decorator
from django.utils.encoding import smart_bytes
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from inloop.gh_import.tasks import update_tasks
from inloop.gh_import.utils import compute_signature

SIGNATURE_HEADER = 'HTTP_X_HUB_SIGNATURE'
GITHUB_SECRET = smart_bytes(settings.GITHUB_SECRET)


class PayloadView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        try:
            signature = request.META[SIGNATURE_HEADER]
        except KeyError:
            return HttpResponseBadRequest('Missing signature')
        my_signature = compute_signature(GITHUB_SECRET, request)
        if not constant_time_compare(signature, my_signature):
            return HttpResponseBadRequest('Invalid signature')
        update_tasks()
        return HttpResponse('Success')
