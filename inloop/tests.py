from unittest import TestCase

from inloop.utils import filter_uppercase_keys


class UtilsTest(TestCase):
    def test_filter_vars(self):
        d = {'foo': 'bar', 'FOO': 'bar', 'KEY': 'value'}
        self.assertEqual(filter_uppercase_keys(d), {'FOO': 'bar', 'KEY': 'value'})
