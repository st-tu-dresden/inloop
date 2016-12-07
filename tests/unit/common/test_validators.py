from unittest import TestCase

from django.core.exceptions import ValidationError

from inloop.common.validators import RegexSyntaxValidator


class RegexSyntaxValidatorTest(TestCase):
    validator = RegexSyntaxValidator()

    def test_invalid_regex(self):
        with self.assertRaises(ValidationError):
            self.validator("a+*")

    def test_valid_regex(self):
        self.validator("valid regex")
