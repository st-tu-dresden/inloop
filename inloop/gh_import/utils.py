import hashlib
import hmac
from os.path import dirname, join
from datetime import datetime

try:
    from shlex import quote
except ImportError:
    from pipes import quote

from django.utils import timezone

# known_hosts file prepopulated with GitHub's pubkeys
HOSTS_FILE = join(dirname(__file__), 'github_known_hosts.txt')


def parse_date(datestr, format='%Y-%m-%d %H:%M:%S'):
    '''Extracts a timezone aware datetime from a string'''
    parsed = datetime.strptime(datestr, format)
    return timezone.make_aware(parsed, timezone.get_current_timezone())


def parse_ssh_url(url):
    parts = {}
    remainder, parts['path'] = url.rsplit(':', 1)
    if '@' in remainder:
        parts['user'], parts['host'] = remainder.split('@')
    else:
        parts['user'], parts['host'] = None, remainder
    return parts


def ssh_options(id_rsa, shell=False, verbose=False):
    opts = [
        '-F/dev/null',
        '-oUserKnownHostsFile=%s' % HOSTS_FILE,
        '-oCheckHostIP=no',
        '-oBatchMode=yes'
    ]
    if id_rsa:
        opts.append('-oIdentityFile=%s' % id_rsa)
    if verbose:
        opts.append('-v')
    if shell:
        return ' '.join([quote(opt) for opt in opts])
    return opts


def compute_signature(secret, data):
    mac = hmac.new(secret, digestmod=hashlib.sha1)
    for chunk in iter(data):
        mac.update(chunk)
    return 'sha1=%s' % mac.hexdigest()
