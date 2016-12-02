import hashlib
import hmac
from os.path import dirname, join
from shlex import quote

# known_hosts file prepopulated with GitHub's pubkeys
HOSTS_FILE = join(dirname(__file__), 'github_known_hosts.txt')


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
