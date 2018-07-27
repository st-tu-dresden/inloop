from django.contrib.sites.models import Site
from django.test import TestCase, override_settings


@override_settings(ROOT_URLCONF="tests.context_processors.urls")
class CurrentSiteContextProcessorTest(TestCase):
    def test_site_attributes(self):
        site = Site.objects.get_current()
        site.name = "Test site"
        site.domain = "example.org"
        site.save()
        response = self.client.get("/current_site_response/")
        self.assertContains(response, "site.name: Test site")
        self.assertContains(response, "site.domain: example.org")
