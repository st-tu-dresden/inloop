from os.path import isabs, join, relpath

from django.conf import settings
from django.http import Http404, HttpResponse
from django.views.static import serve


def sendfile_nginx(request, path, document_root=None):
    """
    Serve a file via Nginx' X-Accel-Redirect header.

    Requires a Nginx internal location to be configured like this:

        location <SENDFILE_NGINX_URL> {
            internal;
            alias <MEDIA_ROOT>;
        }

    (replace with the values from the production settings module)

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
    filename_rel = relpath(filename, settings.MEDIA_ROOT)

    # send the path relative to MEDIA_ROOT, prefixed with Nginx' location
    response = HttpResponse()
    response["X-Accel-Redirect"] = join(settings.SENDFILE_NGINX_URL, filename_rel)

    # we rely on nginx to set all approprioate headers (mime type, length, mod time etc.)
    if 'Content-Type' in response:
        del response['Content-Type']

    return response


def select_sendfile():
    """
    Assign the sendfile() implementation specified by settings.SENDFILE_METHOD.
    """
    method = getattr(settings, "SENDFILE_METHOD", "django")
    if method == "django":
        return serve
    elif method == "nginx":
        return sendfile_nginx
    else:
        raise NotImplemented("Unknown SENDFILE_METHOD %s" % method)


sendfile = select_sendfile()
