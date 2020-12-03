#
# This file contains code taken from or based on Mozilla's Kuma
# project, which is available on github.com/mozilla/kuma.
#


from typing import Callable

from django.http import HttpRequest, HttpResponse


class SetRemoteAddrFromForwardedFor:
    """
    Middleware that sets REMOTE_ADDR based on HTTP_X_FORWARDED_FOR, if the
    latter is set. This is useful if you're sitting behind a reverse proxy that
    causes each request's REMOTE_ADDR to be set to 127.0.0.1.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        try:
            forwarded_for = request.META["HTTP_X_FORWARDED_FOR"]
        except KeyError:
            pass
        else:
            # HTTP_X_FORWARDED_FOR can be a comma-separated list of IPs.
            # The client's IP will be the first one.
            forwarded_for = forwarded_for.split(",")[0].strip()
            request.META["REMOTE_ADDR"] = forwarded_for

        return self.get_response(request)
