from django.test import RequestFactory, SimpleTestCase

from inloop.common.middleware import SetRemoteAddrFromForwardedFor


class SetRemoteAddrFromForwardedForTestCase(SimpleTestCase):
    def test_x_forwarded_for(self):
        rf = RequestFactory()
        middleware = SetRemoteAddrFromForwardedFor()

        req1 = rf.get("/", HTTP_X_FORWARDED_FOR="1.1.1.1")
        middleware.process_request(req1)
        self.assertEqual(req1.META["REMOTE_ADDR"], "1.1.1.1")

        req2 = rf.get("/", HTTP_X_FORWARDED_FOR="2.2.2.2")
        middleware.process_request(req2)
        self.assertEqual(req2.META["REMOTE_ADDR"], "2.2.2.2")

        req3 = rf.get("/", HTTP_X_FORWARDED_FOR="3.3.3.3, 4.4.4.4")
        middleware.process_request(req3)
        self.assertEqual(req3.META["REMOTE_ADDR"], "3.3.3.3")
