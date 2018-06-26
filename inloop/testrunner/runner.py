import logging
import os
import signal
import subprocess
import tempfile
import time
import uuid
from collections import namedtuple
from os.path import isabs, isdir, isfile, join, normpath, realpath

LOG = logging.getLogger(__name__)


def collect_files(path):
    """
    Collect files in the directory specified by path non-recursively into a dict,
    mapping filename to file content.
    """
    retval = dict()
    files = [f for f in os.listdir(path) if isfile(join(path, f))]
    for filename in files:
        with open(join(path, filename), encoding="utf-8") as f:
            retval[filename] = f.read()
    return retval


TestOutput = namedtuple("TestOutput", "rc stdout stderr duration files")
TestOutput.__doc__ = "Container type wrapping the outputs of a test run."


class DockerTestRunner:
    """
    Tester implementation using a local `docker` binary.

    The tester is only responsible for executing the specified image using
    the provided inputs and for collecting the outputs. Interpretation of the
    output must be handled in a separate stage.

    Communication is achieved using:

        - command line arguments
        - stdout/stderr unix pipes
        - process return codes
        - file sharing via mounted volumes

    This class expects that the Docker image specified by image_name has already
    been built (e.g., during the import of a task repository).
    """

    def __init__(self, config, image_name):
        """
        Initialize the tester with a dict-like config and the name of the Docker image.

        The following config keywords are supported:

            - timeout: maximum runtime of a container in seconds (default: 30)
            - memory:  maximum memory a container may use, passed in as string
                       to the Docker CLI as --memory=XXX (defaut: 256m)
            - fssize:  the size of the mounted scratch file system (default: 32m)
        """
        self.config = config
        self.image_name = image_name

    def ensure_absolute_dir(self, path):
        """
        Tests if the given path is absolute and a directory, raises ValueError otherwise.
        """
        if not isabs(path):
            raise ValueError("not an absolute path: %s" % path)
        if not isdir(path):
            raise ValueError("not a directory: %s" % path)

    def check_task(self, task_name, input_path):
        """
        Execute a check for the given task name using the files under the path specified
        by input_path.

        The method blocks as long as the `docker` subprocess has not returned. The child
        may be force-killed after certain resource limits (time, memory, etc.) have been
        reached.

        Returns a TestOutput tuple.
        """
        self.ensure_absolute_dir(input_path)

        # output_path will be a private and unique directory bind mounted to /checker/output
        # inside the container. To allow users other than root to write outputs, we create
        # a world-writable subdirectory called "storage" (because a world-writable mount
        # point would have security implications).
        with tempfile.TemporaryDirectory() as output_path:
            # Resolve symbolic links:
            # On OS X, TMPDIR is set to some random subdir of /var/folders, which
            # resolves to /private/var/folders. Docker for Mac only accepts the
            # resolved path for bind mounts (because it whitelists /private).
            output_path = realpath(output_path)
            self.ensure_absolute_dir(output_path)

            os.chmod(output_path, mode=0o755)
            storage_dir = join(output_path, "storage")
            os.mkdir(storage_dir)
            os.chmod(storage_dir, mode=0o1777)

            start_time = time.perf_counter()
            rc, stdout, stderr = self.communicate(task_name, input_path, output_path)
            duration = time.perf_counter() - start_time
            files = collect_files(storage_dir)

        return TestOutput(rc, stdout, stderr, duration, files)

    def subpath_check(self, path1, path2):
        """
        Tests if paths are not a subdirectory of each other, raises ValueError otherwise.
        """
        path1 = normpath(path1)
        path2 = normpath(path2)
        if path1.startswith(path2) or path2.startswith(path1):
            raise ValueError("a mountpoint must not be a subdirectory of another mountpoint")

    def communicate(self, task_name, input_path, output_path):
        """
        Creates the container and communicates inputs and outputs.
        """
        self.subpath_check(input_path, output_path)
        ctr_id = uuid.uuid4()
        # Setting --hostname=localhost is necessary in addition to --net=none,
        # otherwise each Ant Junit batch test takes about 5 seconds on Alpine
        # Linux based images (Ant tries to resolve the container's hostname).
        args = [
            "docker",
            "run",
            "--rm",
            "--read-only",
            "--net=none",
            "--hostname=localhost",
            "--memory=%s" % self.config.get("memory", "256m"),
            "--volume=%s:/checker/input:ro" % input_path,
            "--volume=%s:/checker/output" % output_path,
            "--tmpfs=/checker/scratch:size=%s" % self.config.get("fssize", "32m"),
            "--name=%s" % ctr_id,
            self.image_name,
            task_name
        ]

        LOG.debug("Popen args: %s", args)

        proc = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        try:
            stdout, stderr = proc.communicate(timeout=self.config.get("timeout", 30))
            rc = proc.returncode
        except subprocess.TimeoutExpired:
            # kills the client
            proc.kill()
            stdout, stderr = proc.communicate()
            rc = signal.SIGKILL
            # the container must be explicitely removed, because
            # SIGKILL cannot be proxied by the docker client
            LOG.debug("removing timed out container %s", ctr_id)
            subprocess.call(["docker", "rm", "--force", str(ctr_id)], stdout=subprocess.DEVNULL)

        stderr = stderr.decode("utf-8", errors="replace")
        stdout = stdout.decode("utf-8", errors="replace")

        LOG.debug("container %s: rc=%r stdout=%r stderr=%r", ctr_id, rc, stdout, stderr)

        if rc in (125, 126, 127):
            # exit codes set exclusively by the Docker daemon
            LOG.error("docker failure (rc=%d): %s", rc, stderr)

        return rc, stdout, stderr
