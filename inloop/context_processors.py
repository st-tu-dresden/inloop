"""
Template context processors for INLOOP.

May be used to inject 'global' variables, like versions etc., into
the template context.
"""
import inloop
from inloop.version import get_git_info


def version(request):
    """
    Adds version information to the context.
    """
    version = inloop.__version__
    branch, commit = get_git_info()
    return {'inloop': locals()}
