"""
Utilities that help identify INLOOP's version.

This module is very much inspired by django.utils.version,
some functions are only slightly modified copies.
"""
from datetime import datetime
from subprocess import check_output
from os.path import dirname

from django.utils.lru_cache import lru_cache


REPO_DIR = dirname(dirname(__file__))


def get_version():
    "Returns a PEP 386-compliant version number for INLOOP."
    from inloop import VERSION as version

    parts = 2 if version[2] == 0 else 3
    main = '.'.join(str(x) for x in version[:parts])

    sub = ''
    if version[3] == 'alpha' and version[4] == 0:
        # Not a tagged version, so we append a timestamp
        git_timestamp = get_git_timestamp()
        if git_timestamp:
            sub = '.git%s' % git_timestamp

    elif version[3] != 'final':
        mapping = {'alpha': 'a', 'beta': 'b', 'rc': 'c'}
        sub = mapping[version[3]] + str(version[4])

    return str(main + sub)


@lru_cache()
def get_git_timestamp():
    "Get the UTC timestamp of the latest git commit."
    try:
        unix_ts = check_output('git log --pretty=format:%ct --quiet -1 HEAD',
                               shell=True, universal_newlines=True, cwd=REPO_DIR)
        timestamp = datetime.utcfromtimestamp(int(unix_ts))
    except:
        return None
    return timestamp.strftime('%Y%m%d%H%M%S')


@lru_cache()
def get_git_info():
    "Returns a tuple (branch name, commit id) identifying the latest git commit."
    try:
        branch = check_output('git rev-parse --abbrev-ref HEAD', shell=True,
                              universal_newlines=True, cwd=REPO_DIR)
        rev = check_output('git rev-parse --short HEAD', shell=True,
                           universal_newlines=True, cwd=REPO_DIR)
        return (branch.strip(), rev.strip())
    except:
        return None


def get_git_info_str():
    "Return git info as a formatted string."
    branch, commit = get_git_info()
    return 'branch: {}, commit: {}'.format(branch, commit)
