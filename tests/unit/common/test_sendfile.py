from django.conf import settings
from django.http import Http404
from django.test import SimpleTestCase, override_settings
from django.test.client import RequestFactory

from inloop.common.sendfile import sendfile_nginx


@override_settings(MEDIA_ROOT=str(settings.PACKAGE_DIR), X_ACCEL_LOCATION="/sendfile")
class NginxSendfileTests(SimpleTestCase):
    def setUp(self):
        # we don't need a valid GET request, but it doesn't hurt either
        factory = RequestFactory()
        self.request = factory.get("/request/to/test.jpg")

        # a subdir of MEDIA_ROOT is a valid docroot
        self.valid_docroot = str(settings.PACKAGE_DIR / "tests")

        # the parent directory of MEDIA_ROOT is not a valid docroot
        self.invalid_docroot = str(settings.PACKAGE_DIR.parent)

    def test_nginx_sendfile(self):
        response = sendfile_nginx(self.request, "test.jpg", self.valid_docroot)
        self.assertEqual(response["X-Accel-Redirect"], "/sendfile/tests/test.jpg")
        self.assertNotIn("Content-Type", response)

    def test_nginx_sendfile_abspath(self):
        with self.assertRaises(ValueError):
            sendfile_nginx(self.request, "/test.jpg", self.valid_docroot)

    def test_nginx_sendfile_nodocroot(self):
        with self.assertRaises(ValueError):
            sendfile_nginx(self.request, "test.jpg")

    def test_nginx_sendfile_not_a_subdir(self):
        with self.assertRaises(Http404):
            sendfile_nginx(self.request, "test.jpg", self.invalid_docroot)
