import os
from subprocess import check_call

from inloop.gh_import.utils import ssh_options

GIT_COMMAND = 'git'
DEFAULT_BRANCH = 'master'


class GitRepository:
    silent_subcmds = ['clone', 'checkout', 'pull']
    keep_envvars = ['PATH', 'LANG', 'LC_ALL', 'USER']

    def __init__(self, git_dir, id_rsa=None, verbose=False):
        self.git_dir = git_dir
        self.id_rsa = id_rsa
        self.verbose = verbose

    def pull(self, git_branch=DEFAULT_BRANCH):
        self._run('checkout', git_branch)
        self._run_with_ssh('pull')

    def clone(self, git_url, git_branch=DEFAULT_BRANCH):
        self._run_with_ssh('clone', '--branch', git_branch, git_url, '.')

    def _clean_env(self):
        env = {}
        for key, val in os.environ.items():
            if key in self.keep_envvars:
                env[key] = val
        return env

    def _run_with_ssh(self, subcmd, *args):
        env = self._clean_env()
        env['GIT_SSH_COMMAND'] = 'ssh {}'.format(
            ssh_options(self.id_rsa, shell=True, verbose=self.verbose)
        )
        self._run(subcmd, *args, env=env)

    def _run(self, subcmd, *args, **kwargs):
        cmd = [GIT_COMMAND, subcmd]
        env = kwargs.get('env', self._clean_env())

        if subcmd in self.silent_subcmds:
            cmd.append('--quiet')
        if args:
            cmd.extend(args)

        return check_call(cmd, env=env, cwd=self.git_dir)
