#
# This file contains code taken from or based on Mozilla's Kuma
# project, which is available on github.com/mozilla/kuma.
#


class SetRemoteAddrFromForwardedFor:
    """
    Middleware that sets REMOTE_ADDR based on HTTP_X_FORWARDED_FOR, if the
    latter is set. This is useful if you're sitting behind a reverse proxy that
    causes each request's REMOTE_ADDR to be set to 127.0.0.1.
    """
    def process_request(self, request):
        try:
            forwarded_for = request.META["HTTP_X_FORWARDED_FOR"]
        except KeyError:
            pass
        else:
            # HTTP_X_FORWARDED_FOR can be a comma-separated list of IPs.
            # The client's IP will be the first one.
            forwarded_for = forwarded_for.split(",")[0].strip()
            request.META["REMOTE_ADDR"] = forwarded_for
