from typing import Any

from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.urls import reverse

from inloop.gitload.secrets import GITHUB_KEY


class Command(BaseCommand):
    help = "Print the settings that should be used to configure the GitHub webhook."

    def handle(self, *args: str, **options: Any) -> None:
        site = Site.objects.get_current()
        url = f"http(s)://{site.domain}{reverse('gitload:webhook_handler')}"
        self.stdout.write(f"Endpoint: {url}")
        self.stdout.write(f"Secret:   {GITHUB_KEY}")
