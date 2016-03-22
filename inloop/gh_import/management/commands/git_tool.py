from optparse import make_option

from django.conf import settings
from django.core.management.base import CommandError, LabelCommand

from inloop.gh_import.git import GitRepository


class Command(LabelCommand):
    help = "Tool to the test git repository Python wrapper and its settings."
    option_list = LabelCommand.option_list + (
        make_option('-i', '--ssh-keyfile', help='Path to your SSH key file [default: %default]',
                    default=settings.GIT_SSH_KEY, metavar='FILE', dest='ssh_keyfile'),
        make_option('-b', '--branch', help='The git branch to use [default: %default]',
                    default=settings.GIT_BRANCH, metavar='BRANCH', dest='git_branch'),
        make_option('-d', '--git-root', help='The local git clone to be used [default: %default]',
                    default=settings.GIT_ROOT, metavar='DIR', dest='git_root')
    )
    label = 'subcommand'
    args = '<subcommand>'

    def handle(self, *labels, **options):
        if not labels or len(labels) != 1:
            raise CommandError('Need exactly one %s' % self.label)
        super().handle(*labels, **options)

    def handle_label(self, subcmd, **options):
        branch = options['git_branch']
        keyfile = options['ssh_keyfile']
        verbose = int(options['verbosity']) >= 2
        root = options['git_root']

        repo = GitRepository(root, keyfile, verbose=verbose)
        if subcmd == 'clone':
            repo.clone(settings.GIT_SSH_URL, branch)
        elif subcmd == 'pull':
            repo.pull(branch)
        else:
            raise CommandError("Invalid subcommand '{}'".format(subcmd))
