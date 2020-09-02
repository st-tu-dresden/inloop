from django.db.models import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.functional import cached_property

from constance import config


class RequireOwnWorkDeclaration:
    def __init__(self, get_response):
        self.get_response = get_response

    @cached_property
    def redirect_url(self):
        return reverse('accounts:confirm_ownwork')

    @cached_property
    def exclude_paths(self):
        return [reverse('login'), reverse('logout'), self.redirect_url]

    def __call__(self, request):
        response = self.get_response(request)
        if not request.user.is_authenticated:
            return response
        if not config.REQUIRE_OWNWORK_DECLARATION:
            return response
        try:
            details = request.user.studentdetails
            if details.ownwork_confirmed:
                return response
        except ObjectDoesNotExist:
            pass
        if request.path not in self.exclude_paths:
            return HttpResponseRedirect(self.redirect_url)
        return response
