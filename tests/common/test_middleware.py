from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase, modify_settings

from inloop.common.middleware import SetRemoteAddrFromForwardedFor


class SetRemoteAddrFromForwardedForTestCase(SimpleTestCase):
    FACTORY = RequestFactory()

    def setUp(self):
        self.middleware = SetRemoteAddrFromForwardedFor(lambda r: HttpResponse())

    def test_x_forwarded_for1(self):
        request = self.FACTORY.get("/", HTTP_X_FORWARDED_FOR="1.1.1.1")
        self.middleware(request)
        self.assertEqual(request.META["REMOTE_ADDR"], "1.1.1.1")

    def test_x_forwarded_for2(self):
        request = self.FACTORY.get("/", HTTP_X_FORWARDED_FOR="3.3.3.3, 4.4.4.4")
        self.middleware(request)
        self.assertEqual(request.META["REMOTE_ADDR"], "3.3.3.3")

    def test_no_x_forwarded_for(self):
        request = self.FACTORY.get("/", REMOTE_ADDR="1.2.3.4")
        self.middleware(request)
        self.assertEqual(request.META["REMOTE_ADDR"], "1.2.3.4")


@modify_settings(MIDDLEWARE={"prepend": "inloop.common.middleware.SetRemoteAddrFromForwardedFor"})
class SetRemoteAddrFromForwardedForIntegrationTest(TestCase):
    """Test the middleware integrates correctly using the Django Test Client."""

    def test_x_forwarded_for_with_client(self):
        request = self.client.get("/", HTTP_X_FORWARDED_FOR="1.1.1.1").wsgi_request
        self.assertEqual(request.META["REMOTE_ADDR"], "1.1.1.1")
