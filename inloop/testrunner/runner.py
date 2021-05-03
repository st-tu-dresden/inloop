import logging
import os
import signal
import subprocess
import time
import uuid
from collections import namedtuple
from os.path import isabs, isdir, join, normpath, realpath
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, Set, Tuple

LOG = logging.getLogger(__name__)


def collect_files(path: str, *, filesize_limit: int) -> Tuple[Dict, Set]:
    """
    Collect files into a dictionary that contains immediate children
    of the given path, mapping file name to file content.
    Ignore files larger than filesize_limit (given in bytes).
    Return a tuple (file_dictionary, ignored_filenames).
    """
    files = {}
    ignored_filenames = set()
    for entry in Path(path).iterdir():
        if not entry.is_file():
            continue
        if entry.stat().st_size > filesize_limit:
            ignored_filenames.add(entry.name)
            continue
        with open(entry) as stream:
            files[entry.name] = stream.read(filesize_limit)
    return files, ignored_filenames


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

    This class expects that the Docker image specified in the config has already
    been built (e.g., during the import of a task repository).
    """

    TRUNCATION_MARKER = b"\n\n[--- output truncated 8< ---]\n"

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the tester with a dict-like config and the name of the Docker image.

        The following config keywords are supported:

            - timeout: maximum runtime of a container in seconds (default: 30)
            - memory:  maximum memory a container may use, passed in as string
                       to the Docker CLI as --memory=XXX (defaut: 256m)
            - fssize:  the size of the mounted scratch file system (default: 32m)
            - image:   the name of the docker image to be used (required, no default)
            - output_limit:
                       the maximum size, in bytes, of the stdout/stderr streams
                       (default: 15000)
            - filesize_limit:
                       the maximum allowed size, in bytes, of individual collected
                       files (default: value of output_limit)
        """
        if "image" not in config:
            raise ValueError("image is a required config key")
        self.config = dict(config)
        self.config.setdefault("timeout", 30)
        self.config.setdefault("memory", "256m")
        self.config.setdefault("fssize", "32m")
        self.config.setdefault("output_limit", 15000)
        self.config.setdefault("filesize_limit", self.config["output_limit"])

    def ensure_absolute_dir(self, path: str) -> None:
        """
        Tests if the given path is absolute and a directory, raises ValueError otherwise.
        """
        if not isabs(path):
            raise ValueError(f"not an absolute path: {path}")
        if not isdir(path):
            raise ValueError(f"not a directory: {path}")

    def check_task(self, task_name: str, input_path: str) -> TestOutput:
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
        with TemporaryDirectory() as output_path:
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
            files, ignored_files = collect_files(
                storage_dir, filesize_limit=self.config["filesize_limit"]
            )
        if len(ignored_files) > 0:
            LOG.info(f"Ignored {len(ignored_files)} output file(s) because they were too large.")
        return TestOutput(rc, stdout, stderr, duration, files)

    def subpath_check(self, path1: str, path2: str) -> None:
        """
        Tests if paths are not a subdirectory of each other, raises ValueError otherwise.
        """
        path1 = normpath(path1)
        path2 = normpath(path2)
        if path1.startswith(path2) or path2.startswith(path1):
            raise ValueError("a mountpoint must not be a subdirectory of another mountpoint")

    def clean_stream(self, stream: bytes) -> str:
        """
        Prepare the stream so it can be processed further in a safe manner.
        Convert bytes to UTF-8.
        If stream exceeds configured size, cut and add a marker.
        """
        limit = self.config["output_limit"]
        if len(stream) > limit:
            stream = stream[:limit] + self.TRUNCATION_MARKER
        return stream.decode("utf-8", errors="replace")

    def communicate(
        self, task_name: str, input_path: str, output_path: str
    ) -> Tuple[int, str, str]:
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
            f"--memory={self.config['memory']}",
            f"--volume={input_path}:/checker/input:ro",
            f"--volume={output_path}:/checker/output",
            f"--tmpfs=/checker/scratch:size={self.config['fssize']}",
            f"--name={ctr_id}",
            self.config["image"],
            task_name,
        ]

        LOG.debug("Popen args: %s", args)

        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        try:
            stdout, stderr = proc.communicate(timeout=self.config["timeout"])
            rc = proc.returncode
        except subprocess.TimeoutExpired:
            # kills the client
            proc.kill()
            stdout, stderr = proc.communicate()
            rc = int(signal.SIGKILL)
            # the container must be explicitely removed, because
            # SIGKILL cannot be proxied by the docker client
            LOG.debug("removing timed out container %s", ctr_id)
            subprocess.call(["docker", "rm", "--force", str(ctr_id)], stdout=subprocess.DEVNULL)

        stderr = self.clean_stream(stderr)
        stdout = self.clean_stream(stdout)

        LOG.debug("container %s: rc=%r stdout=%r stderr=%r", ctr_id, rc, stdout, stderr)

        if rc in (125, 126, 127):
            # exit codes set exclusively by the Docker daemon
            LOG.error("docker failure (rc=%d): %s", rc, stderr)

        return rc, stdout, stderr
