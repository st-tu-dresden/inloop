from optparse import make_option
from os.path import splitext
from subprocess import STDOUT, CalledProcessError, check_output

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from inloop.gh_import.utils import parse_ssh_url, ssh_options


class Command(BaseCommand):
    help = 'Check if the SSH key is correctly setup to connect to GitHub.'
    option_list = BaseCommand.option_list + (
        make_option('-i', '--ssh-keyfile', help='Path to your SSH key file [default: %default]',
                    default=settings.GIT_SSH_KEY, metavar='FILE', dest='ssh_keyfile'),
    )

    def handle(self, *args, **options):
        parts = parse_ssh_url(settings.GIT_SSH_URL)
        keyfile = options['ssh_keyfile']
        verbose = int(options['verbosity']) >= 2

        call_args = ['ssh', '-T']
        call_args.extend(ssh_options(keyfile, verbose=verbose))
        call_args.append('{user}@{host}'.format(**parts))

        try:
            check_output(call_args, env={}, universal_newlines=True, stderr=STDOUT)
        except CalledProcessError as e:
            if e.output:
                self.stdout.write(e.output)

            # The Github greeting returns with status=1 if everything works
            if e.returncode != 1:
                raise CommandError(e)

            # The Github greeting contains the path to the repository to which the deploy
            # key was added (without the trailing '.git'). We warn the user if the value
            # from the settings module doesn't match:
            path, __ = splitext(parts['path'])
            if e.output and path not in e.output:
                self.stderr.write("WARNING: the greeting doesn't mention {}!".format(path))
