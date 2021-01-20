from typing import Dict

from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpRequest


def current_site(request: HttpRequest) -> Dict[str, Site]:
    """Context processor which populates the current site as ``site``."""
    return {"site": get_current_site(request)}
