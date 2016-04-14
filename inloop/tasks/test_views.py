from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import TestCase, RequestFactory
from django.views.generic import View

from inloop.accounts.models import UserProfile
from inloop.tasks.views_new import LoginRequiredMixin


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
