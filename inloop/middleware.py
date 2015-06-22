from .version import get_version, get_git_info_str


class VersionInfoMiddleware():
    "Add version information to request.META in case an uncaught error occurs."
    def process_exception(self, request, exception):
        request.META['INLOOP_VERSION'] = '{} ({})'.format(get_version(), get_git_info_str())
