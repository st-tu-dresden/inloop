from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import TestCase, RequestFactory
from django.utils.encoding import force_text

from django.views.generic import View

from inloop.accounts.models import UserProfile
from inloop.tasks.views import LoginRequiredMixin
from inloop.tasks.test_base import TasksTestBase


class LoginRequiredMixinTest(TestCase):
    factory = RequestFactory()

    def test_protected_view(self):
        class ProtectedView(LoginRequiredMixin, View):
            def get(self, request):
                return HttpResponse()

        protected_view = ProtectedView.as_view()
        request = self.factory.get("/path")
        request.user = AnonymousUser()

        response = protected_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual("/?next=/path", response.url)

        request = self.factory.get("/path")
        request.user = UserProfile.objects.create(username='joe', password='qwerty')
        response = protected_view(request)
        self.assertEqual(response.status_code, 200)


class SolutionStatusViewTest(TasksTestBase):
    def setUp(self):
        super().setUp()
        self.another_user = self.create_user("Bruce Lee")
        self.solution = self.create_solution()

    def test_pending_state(self):
        self.client.login(username="chuck_norris", password="s3cret")
        response = self.client.get("/tasks/solution/%d/status" % self.solution.id)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_text(response.content),
            '{"status": "pending", "solution_id": %d}' % self.solution.id
        )

    def test_only_owner_can_access(self):
        self.client.login(username="bruce_lee", password="s3cret")
        response = self.client.get("/tasks/solution/%d/status" % self.solution.id)
        self.assertEqual(response.status_code, 404)
