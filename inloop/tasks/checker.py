import logging
import os
import signal
import subprocess
import tempfile
import time
import uuid
from collections import namedtuple
from os.path import isabs, isdir, isfile, join, normpath


LOGGER = logging.getLogger(__name__)


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


class DockerSubProcessChecker:
    """
    Checker implementation using a local `docker` binary.

    The checker is only responsible for executing the specified image using
    the provided inputs and for collecting the outputs. Interpretation of the
    output must be handled in a separate stage.

    Communication is achieved using:

        - command line arguments
        - stdout/stderr unix pipes
        - process return codes
        - file sharing via mounted volumes

    Each task repository must provide a Dockerfile. The resulting Docker image
    is expected to be self-contained and must implement the following interface:

      1. A non-zero return code indicates that the check failed for some reason.
         Possible reasons include: failed compilation, failed unit test, internal
         error due to misconfiguration/crash.

      2. The image must provide an entrypoint that accepts the task name as one
         and only argument.

      3. The image mounts a read-only VOLUME at the path:

            /checker/input

         This is the place where user-submitted files are dropped.

         Caveat: The hierarchy of the dropped files currently is flat, i.e., there
         are *no* subdirectories and there is currently no way to specify them.

      4. The image mounts a writable VOLUME at the path

            /checker/output

         containing a world-writable directory "storage". On the host, this is a
         private directory bound to one container.

         This is the place where the different execution stages can drop their
         output as files (e.g., unit test result XML files, Findbug reports).

      5. The rootfs of the container is mounted read-only. To store intermediate
         results such as compiled class files, the scratch tmpfs at

            /checker/scratch

         must be used.

      6. The image may output diagnostic information via stdout or stderr, which
         will be saved for later examination.

    This class expects that the Docker image specified by image_name has already
    been built (e.g., during the import of a task repository).
    """
    Result = namedtuple("DockerSubProcessCheckerResult", "rc stdout stderr duration file_dict")

    def __init__(self, config, image_name):
        """
        Initialize the checker with a dict-like config and the name of the Docker image.

        The following config keywords are supported:

            - timeout: maximum runtime of a container in seconds (default: 30)
            - tmpdir:  directory where we should store temporary files
                       (default: platform-dependent)
        """
        tmpdir = config.get("tmpdir")
        if tmpdir:
            self.ensure_absolute_dir(tmpdir)

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

        Returns a Result tuple.
        """
        self.ensure_absolute_dir(input_path)

        # output_path will be a private and unique directory bind mounted to /checker/output
        # inside the container. To allow users other than root to write outputs, we create
        # a world-writable subdirectory called "storage" (because a world-writable mount
        # point would have security implications).
        with tempfile.TemporaryDirectory(dir=self.config.get("tmpdir")) as output_path:
            self.ensure_absolute_dir(output_path)

            os.chmod(output_path, mode=0o755)
            storage_dir = join(output_path, "storage")
            os.mkdir(storage_dir)
            os.chmod(storage_dir, mode=0o1777)

            start_time = time.perf_counter()
            rc, stdout, stderr = self.communicate(task_name, input_path, output_path)
            duration = time.perf_counter() - start_time
            file_dict = collect_files(storage_dir)

        return self.Result(rc, stdout, stderr, duration, file_dict)

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
        args = [
            "docker",
            "run",
            "--rm",
            # TODO: activate this when the Docker image switched to ant
            # "--read-only",
            "--net=none",
            "--memory=128m",
            "--volume=%s:/checker/input:ro" % input_path,
            "--volume=%s:/checker/output" % output_path,
            "--tmpfs=/checker/scratch",
            "--name=%s" % ctr_id,
            self.image_name,
            task_name
        ]

        LOGGER.debug("Popen args: %s", args)

        proc = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )

        try:
            stdout, stderr = proc.communicate(timeout=self.config.get("timeout", 30))
            rc = proc.returncode
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            rc = signal.SIGKILL
            # kill container *and* the client process (SIGKILL is not proxied)
            subprocess.call(["docker", "rm", "--force", str(ctr_id)])

        if rc in (125, 126, 127):
            # exit codes set exclusively by the Docker daemon
            LOGGER.error("docker failure (rc=%d): %s", rc, stderr)

        return (rc, stdout, stderr)
