from os.path import dirname, join
from shlex import quote
from datetime import datetime

from django.utils import timezone
from markdown import markdown

# known_hosts file prepopulated with GitHub's pubkeys
HOSTS_FILE = join(dirname(__file__), 'github_known_hosts.txt')
MARKDOWN_EXTS = ['markdown.extensions.toc']


def md_load(md_file):
    with open(md_file) as fd:
        return markdown(fd.read(), extensions=MARKDOWN_EXTS)


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
