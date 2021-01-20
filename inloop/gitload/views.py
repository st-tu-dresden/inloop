import hashlib
import hmac
import json
from json import JSONDecodeError
from typing import Dict

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.utils.crypto import constant_time_compare, force_bytes
from django.views.decorators.csrf import csrf_exempt

from constance import config

from inloop.gitload.secrets import GITHUB_KEY
from inloop.gitload.tasks import load_tasks_async


class InvalidSignature(Exception):
    pass


def compute_signature(data: bytes, key: bytes) -> str:
    """Return a GitHub compatible hexadecimal representation of HMAC-SHA1(key, data)."""
    mac = hmac.new(key, msg=data, digestmod=hashlib.sha1)
    return "sha1=%s" % mac.hexdigest()


def safe_json_load(request: HttpRequest) -> Dict[str, str]:
    """Verify the request and return the deserialized request body."""
    signature = request.META.get("HTTP_X_HUB_SIGNATURE")
    expected = compute_signature(request.body, force_bytes(GITHUB_KEY))
    if not constant_time_compare(signature, expected):
        raise InvalidSignature
    return json.loads(request.body)


@csrf_exempt
def webhook_handler(request: HttpRequest) -> HttpResponse:
    """Handle GitHub webhook requests."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        event = request.META.get("HTTP_X_GITHUB_EVENT")
        if event == "push" and request.content_type == "application/json":
            payload = safe_json_load(request)
            configured_ref = f"refs/heads/{config.GITLOAD_BRANCH}"
            if config.GITLOAD_URL and payload.get("ref") == configured_ref:
                load_tasks_async()
                return HttpResponse()
    except JSONDecodeError:
        return HttpResponseBadRequest("Malformed payload.")
    except InvalidSignature:
        return HttpResponseBadRequest("Invalid or missing signature.")
    return HttpResponse(b"Event ignored")
