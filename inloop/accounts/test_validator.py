from django.core.exceptions import ValidationError
from django.test import TestCase

from inloop.accounts.validators import validate_zih_mail


class ZIHMailValidatorTests(TestCase):
    def test_valid_mails(self):
        validate_zih_mail("s4810525@mail.zih.tu-dresden.de")
        validate_zih_mail("martin.morgenstern1@mailbox.tu-dresden.de")
        validate_zih_mail("martin.morgenstern1@tu-dresden.de")

    def test_invalid_maildomain(self):
        with self.assertRaises(ValidationError):
            validate_zih_mail("chuck.norris@example.com")

    def test_invalid_mailformat(self):
        with self.assertRaises(ValidationError):
            validate_zih_mail("chuck.norris@example.com@tu-dresden.de")

    def test_empty_user(self):
        with self.assertRaises(ValidationError):
            validate_zih_mail("@tu-dresden.de")

    def test_invalid_studentno(self):
        with self.assertRaises(ValidationError):
            validate_zih_mail("s123456@mail.zih.tu-dresden.de")
