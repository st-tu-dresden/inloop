import os
import subprocess
import sys
from unittest import mock, TestCase

from inloop.core.utils import changedir, timelimit, filter_uppercase_keys


class UtilsTest(TestCase):
    def test_filter_vars(self):
        d = {'foo': 'bar', 'FOO': 'bar', 'KEY': 'value'}
        self.assertEqual(filter_uppercase_keys(d), {'FOO': 'bar', 'KEY': 'value'})


class ContextManagerTests(TestCase):
    class TestException(Exception):
        """Exception used in some chdir tests."""
        pass

    def test_chdir_exception(self):
        """Test if cwd gets restored even if an exception occurs in the with block."""
        with mock.patch("inloop.core.utils.os.chdir") as patched_chdir:
            with self.assertRaises(self.TestException):
                current_dir = os.getcwd()
                with changedir("/some/path"):
                    patched_chdir.assert_called_with("/some/path")
                    raise self.TestException
            patched_chdir.assert_called_with(current_dir)

    def test_timelimit(self):
        proc = subprocess.Popen([sys.executable, '-c', "while True: pass"])
        with timelimit(0.01, lambda: proc.kill()):
            proc.communicate()
        self.assertEqual(proc.returncode, -9)
