from django.contrib.sites.shortcuts import get_current_site


def current_site(request):
    """Context processor which populates the current site as ``site``."""
    return {
        'site': get_current_site(request)
    }
