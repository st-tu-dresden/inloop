from django.test import RequestFactory, SimpleTestCase

from inloop.common.middleware import SetRemoteAddrFromForwardedFor


class SetRemoteAddrFromForwardedForTestCase(SimpleTestCase):
    rf = RequestFactory()

    def test_x_forwarded_for(self):
        middleware = SetRemoteAddrFromForwardedFor()
        req1 = self.rf.get("/", HTTP_X_FORWARDED_FOR="1.1.1.1")
        middleware.process_request(req1)
        self.assertEqual(req1.META["REMOTE_ADDR"], "1.1.1.1")

        req2 = self.rf.get("/", HTTP_X_FORWARDED_FOR="3.3.3.3, 4.4.4.4")
        middleware.process_request(req2)
        self.assertEqual(req2.META["REMOTE_ADDR"], "3.3.3.3")

    def test_no_x_forwarded_for(self):
        middleware = SetRemoteAddrFromForwardedFor()
        req = self.rf.get("/")
        req.META["REMOTE_ADDR"] = "1.2.3.4"
        middleware.process_request(req)
        self.assertEqual(req.META["REMOTE_ADDR"], "1.2.3.4")
