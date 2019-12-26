from django.core.exceptions import ValidationError
from django.test import TestCase

from constance.test import override_config

from inloop.solutions.validators import _get_allowed_filename_extensions, validate_filenames


@override_config(ALLOWED_FILENAME_EXTENSIONS='.java   ,  .b ,.cpp,  \n.h,\r.py')
class FileNameExtensionValidationTest(TestCase):
    def test_get_allowed_filename_extensions(self):
        filename_extensions = _get_allowed_filename_extensions()
        self.assertEqual(['.java', '.b', '.cpp', '.h', '.py'], filename_extensions)

    def test_valid_filenames(self):
        filenames = [
            'HelloWorld.java',
            'HelloWorld.b',
            'HelloWorld.cpp',
            'HelloWorld.h',
            'HelloWorld.py'
        ]
        try:
            validate_filenames(filenames)
        except ValidationError as e:
            self.fail('Filename validation should succeed on the '
                      'given files. ({})'.format(e.message))

    def test_invalid_filenames(self):
        filenames = ['HelloWorld.kt']
        with self.assertRaises(ValidationError):
            validate_filenames(filenames)

    def test_no_filenames(self):
        with self.assertRaises(ValidationError):
            validate_filenames([])

    def test_case_insensitivity(self):
        filenames = [
            'First.java',
            'Second.JAVA',
            'Third.jAvA'
        ]
        try:
            validate_filenames(filenames)
        except ValidationError:
            self.fail('Filename validation should be case insensitive')


@override_config(ALLOWED_FILENAME_EXTENSIONS='')
class EmptyAllowedFileNameExtensionsValidationTest(TestCase):
    def test_get_allowed_filename_extensions(self):
        filename_extensions = _get_allowed_filename_extensions()
        self.assertEqual([], filename_extensions)

    def test_filenames(self):
        filenames = ['HelloWorld.java']
        with self.assertRaises(ValidationError):
            validate_filenames(filenames)
