import os
import subprocess
import shutil
from os.path import dirname, join
from unittest import skipUnless

from django.test import TestCase

from inloop.tasks.docker import collect_files, DockerSubProcessChecker


TEST_DIR = join(dirname(__file__), "tests")


class CollectorTest(TestCase):
    test_harness = join(TEST_DIR, "file_dict")

    def test_collected_names(self):
        filenames = collect_files(self.test_harness).keys()
        self.assertEqual(len(filenames), 2)
        self.assertIn("empty1.txt", filenames)
        self.assertIn("README.md", filenames)
        self.assertNotIn("should_be_ignored", filenames)
        self.assertNotIn("empty2.txt", filenames)

    def test_collected_contents(self):
        file_dict = collect_files(self.test_harness)
        self.assertEqual("", file_dict["empty1.txt"])
        self.assertEqual("This is a test harness for collect_files().\n", file_dict["README.md"])


@skipUnless(shutil.which("docker"), "Docker is not installed.")
class DockerSubProcessCheckerTests(TestCase):
    image_name = "inloop-integration-test"

    # docker-machine on OS X needs a mount point below $HOME
    options = {
        "timeout": 1,
        "tmpdir": join(TEST_DIR, ".tmp_docker")
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.makedirs(cls.options["tmpdir"], exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.options["tmpdir"])
        super().tearDownClass()

    def setUp(self):
        self.checker = DockerSubProcessChecker(self.options, self.image_name)

    def test_selftest(self):
        """Test if our test image works."""
        rc = subprocess.call(["docker", "run", "--rm", self.image_name, "exit 42"])
        self.assertEqual(42, rc)
