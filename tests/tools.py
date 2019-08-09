import os
import shutil
from tempfile import mkdtemp

from django.test import TestCase, override_settings

TEST_MEDIA_ROOT = mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class TemporaryMediaRootTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not os.path.isdir(TEST_MEDIA_ROOT):
            os.makedirs(TEST_MEDIA_ROOT)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_MEDIA_ROOT)
        super().tearDownClass()
