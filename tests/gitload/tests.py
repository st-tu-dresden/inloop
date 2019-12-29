from pathlib import Path
from subprocess import check_output
from tempfile import TemporaryDirectory
from unittest import TestCase

from django.test import tag

from inloop.gitload.repo import GitRepository


@tag('slow')
class GitRepositoryTest(TestCase):
    def setUp(self):
        self.tmpdir = TemporaryDirectory()
        self.repo1 = GitRepository(
            self.tmpdir.name,
            url='https://github.com/st-tu-dresden/inloop.git',
            branch='master'
        )
        self.repo2 = GitRepository(
            self.tmpdir.name,
            url='https://github.com/st-tu-dresden/inloop-java-repository-example.git',
            branch='master'
        )

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_git_operations(self):
        self.repo1.synchronize()
        self.assertTrue(self.get_path('.git').exists())
        self.assertTrue(self.get_path('manage.py').exists())
        self.assertEqual(b'', self.run_command('git status -s'))

        self.repo2.synchronize()
        self.assertFalse(self.get_path('manage.py').exists())
        self.assertTrue(self.get_path('build.xml').exists())
        self.assertEqual(b'', self.run_command('git status -s'))

    def get_path(self, name):
        return Path(self.tmpdir.name, name)

    def run_command(self, command):
        return check_output(command.split(), cwd=self.tmpdir.name)
