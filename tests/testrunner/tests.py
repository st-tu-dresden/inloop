import signal
import subprocess
import sys
from pathlib import Path
from unittest import TestCase, skipIf

from django.test import tag

from inloop.testrunner.runner import DockerTestRunner, collect_files

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = str(BASE_DIR.joinpath("data"))


class CollectorTest(TestCase):
    def test_subdirs_and_large_files_are_not_collected(self):
        contents, ignored_names = collect_files(DATA_DIR, filesize_limit=300)
        self.assertEqual(contents.keys(), {"empty1.txt", "README.md"})
        self.assertEqual(ignored_names, {"larger_than_300_bytes.txt"})

    def test_subdirs_are_not_collected(self):
        contents, ignored_names = collect_files(DATA_DIR, filesize_limit=1000)
        self.assertEqual(contents.keys(), {"empty1.txt", "README.md", "larger_than_300_bytes.txt"})
        self.assertFalse(ignored_names)

    def test_collected_contents_are_correct(self):
        contents, _ = collect_files(DATA_DIR, filesize_limit=300)
        self.assertEqual(contents["empty1.txt"], "")
        self.assertEqual(contents["README.md"], "This is a test harness for collect_files().\n")


@tag("slow", "needs-docker")
class DockerTestRunnerIntegrationTest(TestCase):
    """
    Each of the the following tests uses a *real* docker container, there is
    no monkey patching (aka mocking) involved.

    The Docker image required for the tests uses a simple trick to allow
    submitting arbitrary test commands to the container using the task_name
    parameter of DockerTestRunner.check_task(). This makes it really
    easy to simulate the behaviors of a real tester image.
    """

    OPTIONS = {
        "image": "inloop-integration-test",
        "timeout": 1.5,
    }

    def setUp(self):
        self.runner = DockerTestRunner(self.OPTIONS)

    def test_selftest(self):
        """Test if our test image works."""
        rc = subprocess.call(["docker", "run", "--rm", self.OPTIONS["image"], "exit 42"])
        self.assertEqual(42, rc)

    def test_outputs(self):
        """Test if we receive stdout, stderr and exit code."""
        result = self.runner.check_task("echo -n OUT; echo -n ERR >&2; exit 42", DATA_DIR)
        self.assertEqual(result.rc, 42)
        self.assertEqual(result.stdout, "OUT")
        self.assertEqual(result.stderr, "ERR")
        self.assertGreaterEqual(result.duration, 0.0)

    @skipIf(sys.platform == "darwin", reason="Docker Desktop issues")
    def test_kill_on_timeout(self):
        """Test if the container gets killed after the timeout."""
        result = self.runner.check_task("sleep 10", DATA_DIR)
        self.assertEqual(result.rc, signal.SIGKILL)
        self.assertGreaterEqual(result.duration, 0.0)
        self.assertLess(result.duration, 10.0)

    @skipIf(sys.platform == "darwin", reason="Docker Desktop issues")
    def test_output_on_timeout(self):
        """Test if we receive output even if a timeout happens."""
        result = self.runner.check_task("echo -n OUT; echo -n ERR >&2; sleep 10", DATA_DIR)
        self.assertEqual(result.rc, signal.SIGKILL)
        self.assertEqual(result.stdout, "OUT")
        self.assertEqual(result.stderr, "ERR")

    def test_inbound_mountpoint(self):
        """Test if the input mount point works correctly."""
        result = self.runner.check_task("cat /checker/input/README.md", DATA_DIR)
        self.assertEqual("This is a test harness for collect_files().\n", result.stdout)
        self.assertEqual(result.rc, 0)

    def test_scratch_area(self):
        """Test that we can write the scratch area."""
        result = self.runner.check_task("touch /checker/scratch/test_file", DATA_DIR)
        self.assertEqual(result.rc, 0)

    def test_inbound_mountpoint_ro(self):
        """Test if the input is mounted read-only."""
        result = self.runner.check_task("touch /checker/input/test_file", DATA_DIR)
        self.assertNotEqual(result.rc, 0)

    def test_storage_exists(self):
        """Test if the storage directory exists."""
        result = self.runner.check_task("test -d /checker/output/storage", DATA_DIR)
        self.assertEqual(result.rc, 0)

    def test_output_filedict(self):
        """Test if we can create a file which appears in the files dictionary."""
        result = self.runner.check_task("echo -n FOO >/checker/output/storage/bar", DATA_DIR)
        self.assertEqual(result.rc, 0)
        self.assertEqual("FOO", result.files["bar"])

    def test_container_unprivileged(self):
        """Test if we execute commands as unprivileged user."""
        result = self.runner.check_task("id -un", DATA_DIR)
        self.assertEqual(result.rc, 0)
        self.assertEqual(result.stdout.strip(), "nobody")

    def test_maximum_file_size(self):
        """Test limits of the scratch file system."""
        result = self.runner.check_task(
            "dd if=/dev/zero of=/checker/scratch/largefile bs=1M count=100", DATA_DIR
        )
        self.assertNotEqual(result.rc, 0)

    def test_scratch_mount_options(self):
        """Verify if the tmpfs is mounted correctly."""
        result = self.runner.check_task("mount | grep 'tmpfs on /checker/scratch'", DATA_DIR)
        # the default size=32m is expanded to kilobytes
        self.assertIn("size=32768k", result.stdout)


class DockerTestRunnerTest(TestCase):
    def setUp(self):
        self.runner = DockerTestRunner(
            {
                "image": "image-not-used",
                "output_limit": 10,
            }
        )

    def test_constructor_requires_configkey(self):
        with self.assertRaises(ValueError):
            DockerTestRunner({})

    # TEST 1: good utf-8 sequence
    def test_clean_stream_with_short_valid_utf8(self):
        sample_stream = "abcöüä".encode()
        cleaned = self.runner.clean_stream(sample_stream)
        self.assertEqual(cleaned, "abcöüä")

    # TEST 2: bogus utf-8 sequence
    def test_clean_stream_with_short_invalid_utf8(self):
        sample_stream = "abcöüä".encode()
        # cut off the right half of the utf8 char at the end ('ä'), making it invalid
        cleaned = self.runner.clean_stream(sample_stream[:-1])
        self.assertEqual(len(cleaned), 6)
        self.assertIn("abcöü", cleaned)

    # TEST 3: good utf-8 sequence, too long
    def test_clean_stream_with_too_long_valid_utf8(self):
        sample_stream = ("a" * 11).encode()
        cleaned = self.runner.clean_stream(sample_stream)
        self.assertNotIn("a" * 11, cleaned)
        self.assertIn("a" * 10, cleaned)
        self.assertIn("output truncated", cleaned)

    # TEST 4: too long utf-8 sequence, utf-8 composite at cut position
    def test_clean_stream_with_utf8_composite_at_cut_position(self):
        sample_stream = "".join(["a", "ä" * 5]).encode()
        cleaned = self.runner.clean_stream(sample_stream)
        self.assertNotIn("ä" * 5, cleaned)
        self.assertIn("aääää", cleaned)
        self.assertIn("output truncated", cleaned)
