from unittest import TestCase

from inloop.grading.tud import guess_name_from_email


class GradingTest(TestCase):
    def test_guessed_emails(self):
        pairs = {
            "chuck.norris@mailbox.tu-dresden.de": ("Chuck", "Norris"),
            "chuck.norris1@mailbox.tu-dresden.de": ("Chuck", "Norris"),
            "ed.van_schleck1@mailbox.tu-dresden.de": ("Ed", "Van Schleck"),
            "s1234567@mail.zih.tu-dresden.de": ("", ""),
            "chuck.norris@tu-dresden.de": ("", ""),
        }
        for email, name in pairs.items():
            self.assertEqual(guess_name_from_email(email), name)
