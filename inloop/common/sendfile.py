from os.path import isabs, join, relpath
from typing import Optional

from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse
from django.views.static import serve


def sendfile_nginx(
    request: HttpRequest, path: str, document_root: Optional[str] = None
) -> HttpResponse:
    """
    Serve a file via Nginx' X-Accel-Redirect header.

    Requires a Nginx internal location to be configured like this:

        location <X_ACCEL_LOCATION> {
            internal;
            alias <MEDIA_ROOT>;
        }

    (replace with the values from the settings module)

    Currently, document_root must be a subdirectory of MEDIA_ROOT and path
    must be relative.
    """
    if isabs(path):
        raise ValueError("path must be relative")

    if not document_root:
        raise ValueError("no document_root given")

    if not document_root.startswith(settings.MEDIA_ROOT):
        # not a subdirectory, there will be no relative path to MEDIA_ROOT
        raise Http404

    # the complete path to the file on the filesystem
    filename = join(document_root, path)

    # the path relative to the MEDIA_ROOT (= alias directive)
    filename_rel = relpath(filename, settings.MEDIA_ROOT).replace("\\", "/")

    # the internal nginx location w/o trailing slashes
    location = getattr(settings, "X_ACCEL_LOCATION", "").rstrip("/")

    # send the path relative to MEDIA_ROOT, prefixed with nginx' location
    response = HttpResponse()
    response["X-Accel-Redirect"] = "/".join([location, filename_rel])

    # we rely on nginx to set all approprioate headers (mime type, length, mod time etc.)
    del response["Content-Type"]

    return response


# Select the sendfile implementation based on the settings:
if hasattr(settings, "X_ACCEL_LOCATION"):
    sendfile = sendfile_nginx
else:
    sendfile = serve
