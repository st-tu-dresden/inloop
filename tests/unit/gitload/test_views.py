from unittest.mock import patch

from django.test import TestCase
from django.test.client import RequestFactory
from django.utils.crypto import force_bytes

from constance.test import override_config

from inloop.gitload.secrets import GITHUB_KEY
from inloop.gitload.views import compute_signature, webhook_handler


class SignatureTest(TestCase):
    def test_github_key_is_alphanumeric_string(self):
        self.assertTrue(isinstance(GITHUB_KEY, str))
        self.assertTrue(GITHUB_KEY.isalnum())

    def test_compute_signature_bytes(self):
        self.assertEqual(
            compute_signature(b"foo", key=b"secret"),
            "sha1=9baed91be7f58b57c824b60da7cb262b2ecafbd2"
        )


@patch("inloop.gitload.views.load_tasks_async")
@override_config(
    # path must be non-empty, but should not be accessed
    # during this test because the function is a mock
    GITLOAD_URL="file:///nonexistent/path/to/repo.git",
    GITLOAD_BRANCH="master"
)
class WebhookHandlerTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.key = force_bytes(GITHUB_KEY)

    def test_get_not_allowed(self, mock):
        request = self.factory.get("/")
        response = webhook_handler(request)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(mock.call_count, 0)

    def test_push_with_valid_signature(self, mock):
        data = b'{"ref": "refs/heads/master"}'
        request = self.factory.post("/", data=data, content_type="application/json")
        request.META["HTTP_X_HUB_SIGNATURE"] = compute_signature(data, self.key)
        request.META["HTTP_X_GITHUB_EVENT"] = "push"
        response = webhook_handler(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock.call_count, 1)

    def test_push_with_invalid_signature(self, mock):
        data = b'{"ref": "refs/heads/master"}'
        request = self.factory.post("/", data=data, content_type="application/json")
        request.META["HTTP_X_HUB_SIGNATURE"] = "invalid"
        request.META["HTTP_X_GITHUB_EVENT"] = "push"
        response = webhook_handler(request)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(b"invalid" in response.content.lower())
        self.assertEqual(mock.call_count, 0)

    def test_not_modified_when_event_not_push(self, mock):
        data = b'{"ref": "refs/heads/master"}'
        request = self.factory.post("/", data=data, content_type="application/json")
        request.META["HTTP_X_HUB_SIGNATURE"] = compute_signature(data, self.key)
        request.META["HTTP_X_GITHUB_EVENT"] = "ping"
        response = webhook_handler(request)
        self.assertContains(response, "Event ignored")
        self.assertEqual(mock.call_count, 0)

    def test_not_modified_when_ref_not_master(self, mock):
        data = b'{"ref": "refs/heads/develop"}'
        request = self.factory.post("/", data=data, content_type="application/json")
        request.META["HTTP_X_HUB_SIGNATURE"] = compute_signature(data, self.key)
        request.META["HTTP_X_GITHUB_EVENT"] = "push"
        response = webhook_handler(request)
        self.assertContains(response, "Event ignored")
        self.assertEqual(mock.call_count, 0)

    def test_push_with_invalid_json(self, mock):
        data = b'<xml-is-not-json/>'
        request = self.factory.post("/", data=data, content_type="application/json")
        request.META["HTTP_X_HUB_SIGNATURE"] = compute_signature(data, self.key)
        request.META["HTTP_X_GITHUB_EVENT"] = "push"
        response = webhook_handler(request)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(b"malformed" in response.content.lower())
        self.assertEqual(mock.call_count, 0)
