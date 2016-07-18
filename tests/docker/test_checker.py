import signal
import subprocess
from pathlib import Path

from django.conf import settings
from django.test import TestCase

from inloop.tasks.checker import DockerSubProcessChecker, collect_files

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = str(BASE_DIR / "data")


class CollectorTest(TestCase):
    def test_collected_names(self):
        filenames = collect_files(DATA_DIR).keys()
        self.assertEqual(len(filenames), 2)
        self.assertIn("empty1.txt", filenames)
        self.assertIn("README.md", filenames)
        self.assertNotIn("should_be_ignored", filenames)
        self.assertNotIn("empty2.txt", filenames)

    def test_collected_contents(self):
        file_dict = collect_files(DATA_DIR)
        self.assertEqual("", file_dict["empty1.txt"])
        self.assertEqual("This is a test harness for collect_files().\n", file_dict["README.md"])


class DockerSubProcessCheckerTests(TestCase):
    """
    Each of the the following tests uses a *real* docker container, there is
    no monkey patching (aka mocking) involved.

    The Docker image required for the tests uses a simple trick to allow
    submitting arbitrary test commands to the container using the task_name
    parameter of DockerSubProcessChecker.check_task(). This makes it really
    easy to simulate the behaviors of a real Checker image.

    See the Dockerfile in inloop/tasks/tests/docker for details.
    """

    # name of the Docker image we use for this test
    image_name = "inloop-integration-test"
    input_path = DATA_DIR

    # NOTE: tmpdir=None means using the platform default (e.g., TMPDIR)
    options = {
        "timeout": 1.5,
        "tmpdir": settings.CHECKER.get("tmpdir")
    }

    def setUp(self):
        self.checker = DockerSubProcessChecker(self.options, self.image_name)

    def test_selftest(self):
        """Test if our test image works."""
        rc = subprocess.call(["docker", "run", "--rm", self.image_name, "exit 42"])
        self.assertEqual(42, rc)

    def test_outputs(self):
        """Test if we receive stdout, stderr and exit code."""
        result = self.checker.check_task(
            "echo -n OUT; echo -n ERR >&2; exit 42",
            self.input_path
        )
        self.assertEqual(result.rc, 42)
        self.assertEqual(result.stdout, "OUT")
        self.assertEqual(result.stderr, "ERR")
        self.assertGreaterEqual(result.duration, 0.0)

    def test_kill_on_timeout(self):
        """Test if the container gets killed after the timeout."""
        result = self.checker.check_task("sleep 10", self.input_path)
        self.assertEqual(result.rc, signal.SIGKILL)
        self.assertGreaterEqual(result.duration, 0.0)
        self.assertLess(result.duration, 10.0)

    def test_output_on_timeout(self):
        """Test if we receive output even if a timeout happens."""
        result = self.checker.check_task(
            "echo -n OUT; echo -n ERR >&2; sleep 10",
            self.input_path
        )
        self.assertEqual(result.rc, signal.SIGKILL)
        self.assertEqual(result.stdout, "OUT")
        self.assertEqual(result.stderr, "ERR")

    def test_inbound_mountpoint(self):
        """Test if the input mount point works correctly."""
        result = self.checker.check_task(
            "cat /checker/input/README.md",
            self.input_path
        )
        self.assertEqual("This is a test harness for collect_files().\n", result.stdout)
        self.assertEqual(result.rc, 0)

    def test_scratch_area(self):
        """Test that we can write the scratch area."""
        result = self.checker.check_task(
            "touch /checker/scratch/test_file",
            self.input_path
        )
        self.assertEqual(result.rc, 0)

    def test_inbound_mountpoint_ro(self):
        """Test if the input is mounted read-only."""
        result = self.checker.check_task(
            "touch /checker/input/test_file",
            self.input_path
        )
        self.assertNotEqual(result.rc, 0)

    def test_storage_exists(self):
        """Test if the storage directory exists."""
        result = self.checker.check_task(
            "test -d /checker/output/storage",
            self.input_path
        )
        self.assertEqual(result.rc, 0)

    def test_output_filedict(self):
        """Test if we can create a file which appears in the file_dict."""
        result = self.checker.check_task(
            "echo -n FOO >/checker/output/storage/bar",
            self.input_path
        )
        self.assertEqual(result.rc, 0)
        self.assertEqual("FOO", result.file_dict["bar"])

    def test_container_unprivileged(self):
        """Test if we execute commands as unprivileged user."""
        result = self.checker.check_task("id -un", self.input_path)
        self.assertEqual(result.rc, 0)
        self.assertEqual(result.stdout.strip(), "nobody")

    def test_maximum_file_size(self):
        """Test limits of the scratch file system."""
        result = self.checker.check_task(
            "dd if=/dev/zero of=/checker/scratch/largefile bs=1M count=100",
            self.input_path
        )
        self.assertNotEqual(result.rc, 0)

    def test_scratch_mount_options(self):
        """Verify if the tmpfs is mounted correctly."""
        result = self.checker.check_task(
            "mount | grep 'tmpfs on /checker/scratch'",
            self.input_path
        )
        # the default size=32m is expanded to kilobytes
        self.assertIn("size=32768k", result.stdout)
