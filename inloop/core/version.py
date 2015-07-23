"""
Utilities that help identify INLOOP's version.

This module is very much inspired by django.utils.version,
some functions are only slightly modified copies.
"""
from datetime import datetime
from subprocess import check_output

from django.utils.lru_cache import lru_cache
from django.conf import settings


@lru_cache()
def get_git_timestamp():
    "Get the UTC timestamp of the latest git commit."
    try:
        unix_ts = check_output('git log --pretty=format:%ct --quiet -1 HEAD', shell=True,
                               universal_newlines=True, cwd=settings.PROJECT_ROOT)
        timestamp = datetime.utcfromtimestamp(int(unix_ts))
    except:
        return None
    return timestamp.strftime('%Y%m%d%H%M%S')


@lru_cache()
def get_git_info():
    "Returns a tuple (branch name, commit id) identifying the latest git commit."
    try:
        branch = check_output('git rev-parse --abbrev-ref HEAD', shell=True,
                              universal_newlines=True, cwd=settings.PROJECT_ROOT)
        rev = check_output('git rev-parse --short HEAD', shell=True,
                           universal_newlines=True, cwd=settings.PROJECT_ROOT)
        return (branch.strip(), rev.strip())
    except:
        return None


def get_git_info_str():
    "Return git info as a formatted string."
    branch, commit = get_git_info()
    return 'branch: {}, commit: {}'.format(branch, commit)
