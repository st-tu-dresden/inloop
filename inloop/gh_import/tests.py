from unittest import TestCase
from unittest.mock import patch, mock_open
from os import path

from django.utils import timezone

from inloop.gh_import.utils import md_load, ssh_options, parse_date, parse_ssh_url
from inloop.gh_import.utils import HOSTS_FILE
from inloop.gh_import.git import GitRepository
from inloop.gh_import import __name__ as PACKAGE


class UtilsTest(TestCase):
    def test_parse_git_ssh_url_with_user(self):
        parts = parse_ssh_url('git@github.com:user/repo.git')
        self.assertEqual(parts['user'], 'git')
        self.assertEqual(parts['host'], 'github.com')
        self.assertEqual(parts['path'], 'user/repo.git')

    def test_parse_git_ssh_url_without_user(self):
        parts = parse_ssh_url('github.com:user/repo.git')
        self.assertEqual(parts['user'], None)
        self.assertEqual(parts['host'], 'github.com')
        self.assertEqual(parts['path'], 'user/repo.git')

    def test_hosts_file_exists(self):
        self.assertTrue(path.exists(HOSTS_FILE))

    def test_parse_date(self):
        with timezone.override(timezone.UTC()):
            d = parse_date('2015-07-22 14:12:59')
        self.assertTrue(timezone.is_aware(d))
        self.assertEqual(d.tzname(), 'UTC')
        self.assertEqual(d.year, 2015)
        self.assertEqual(d.month, 7)
        self.assertEqual(d.day, 22)
        self.assertEqual(d.hour, 14)
        self.assertEqual(d.minute, 12)
        self.assertEqual(d.second, 59)

    def test_ssh_options_shell_quoting(self):
        opts_space = ssh_options('path with spaces', shell=True)
        self.assertTrue(isinstance(opts_space, str))
        self.assertTrue("'-oIdentityFile=path with spaces'" in opts_space)
        self.assertFalse('-v' in opts_space)

    def test_ssh_options_args(self):
        opts = ssh_options(None, shell=True, verbose=True)
        self.assertTrue(isinstance(opts, str))
        self.assertTrue('IdentityFile' not in opts)
        self.assertTrue('-v' in opts)

    def test_ssh_options_noshell(self):
        opts = ssh_options(None, shell=False)
        self.assertTrue(isinstance(opts, list))

    @patch('%s.utils.open' % PACKAGE, mock_open(read_data='# Heading'), create=True)
    def test_md_load(self):
        markdown = md_load('path/to/file.md')
        self.assertTrue('<h1 id="heading">' in markdown)
        self.assertTrue('Heading' in markdown)


@patch('%s.git.check_call' % PACKAGE)
class GitRepositoryTest(TestCase):
    def setUp(self):
        self.repo = GitRepository('path/to/repo')

    def test_clone(self, mock):
        self.repo.clone('user@host:repo.git', git_branch='test_branch')
        args, kwargs = mock.call_args

        self.assertEqual(kwargs['cwd'], 'path/to/repo')
        self.assertTrue('GIT_SSH_COMMAND' in kwargs['env'].keys())

        cmd_list = args[0]
        self.assertEqual(cmd_list[:2], ['git', 'clone'])
        self.assertEqual(cmd_list[-1], '.')
        self.assertTrue('user@host:repo.git' in cmd_list)
        self.assertEqual(cmd_list.index('test_branch') - cmd_list.index('--branch'), 1)

    def test_pull(self, mock):
        self.repo.pull('test_branch')
        self.assertEqual(mock.call_count, 2)

        args1, kwargs1 = mock.call_args_list[0]
        cmd_list1 = args1[0]
        self.assertEqual(cmd_list1[:2], ['git', 'checkout'])
        self.assertTrue('test_branch' in cmd_list1)
        self.assertFalse('GIT_SSH_COMMAND' in kwargs1['env'].keys())

        args2, kwargs2 = mock.call_args_list[1]
        cmd_list2 = args2[0]
        self.assertEqual(cmd_list2[:2], ['git', 'pull'])
        self.assertTrue('GIT_SSH_COMMAND' in kwargs2['env'].keys())
