from unittest import TestCase

from django.core.exceptions import ValidationError

from inloop.common.validators import RegexSyntaxValidator


class RegexSyntaxValidatorTest(TestCase):
    def setUp(self):
        self.validate = RegexSyntaxValidator()

    def test_invalid_regex(self):
        with self.assertRaises(ValidationError):
            self.validate("a+*")

    def test_valid_regex(self):
        self.validate("valid regex")
