import logging
import os
import signal
import string
import subprocess
import tempfile
import time
import uuid
import xml.etree.ElementTree as ET
from collections import namedtuple
from os.path import isdir, isfile, join
from random import SystemRandom
from subprocess import STDOUT, CalledProcessError, TimeoutExpired, check_output

from django.conf import settings

from inloop.tasks.models import CheckerResult, TaskSolution


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
        self.config = config
        self.image_name = image_name

    def check_task(self, task_name, input_path):
        """
        Execute a check for the given task name using the files under the path specified
        by input_path.

        The method blocks as long as the `docker` subprocess has not returned. The child
        may be force-killed after certain resource limits (time, memory, etc.) have been
        reached.

        Returns a Result tuple.
        """
        if not isdir(input_path):
            raise ValueError("Not a directory: %s" % input_path)

        # output_path will be private and unique directory bind mounted to /checker/output
        # inside the container. To allow users other than root to write outputs, we create
        # a world-writable subdirectory called "storage" (because a world-writable mount
        # point would have security implications).
        with tempfile.TemporaryDirectory(dir=self.config.get("tmpdir")) as output_path:
            start_time = time.perf_counter()
            storage_dir = join(output_path, "storage")
            os.mkdir(storage_dir, mode=0o777)
            rc, stdout, stderr = self.communicate(task_name, input_path, output_path)
            duration = time.perf_counter() - start_time
            file_dict = collect_files(storage_dir)

        return self.Result(rc, stdout, stderr, duration, file_dict)

    def communicate(self, task_name, input_path, output_path):
        """
        Creates the container and communicates inputs and outputs.
        """
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


# TODO: remove coupling to django and our models
class Checker:
    def __init__(self, solution):
        self.solution = solution
        self.solution_path = self.solution.solution_path()

    def start(self):
        logging.debug("Checker start call")
        ctr_name = self._generate_container_name()
        # self._container_build(ctr_tag='docker-test')
        result, ce = self._container_execute(
            ctr_tag=settings.CHECKER['Container'].get('container_tag'),
            ctr_name=ctr_name,
            cmd=self.solution.task.name,
            mountpoints={
                self.solution_path: settings.CHECKER['Container'].get('solution_path')
            })
        self._parse_result(result, ce)

    def _generate_container_name(self):
        charset = string.ascii_letters + string.digits
        length = 21
        random = SystemRandom()
        key = "".join(random.sample(charset, length))
        return "-".join([str(self.solution.author.username), str(self.solution.task.slug), key])

    def _container_build(self, ctr_tag, path="."):
        logging.debug("Container build process started")
        build_cmd = ['docker', 'build', '-t', ctr_tag, '--rm=true', path]
        try:
            build_output = check_output(
                build_cmd,
                stderr=STDOUT,
                timeout=settings.CHECKER['Timeouts'].get('container_build'),
                shell=True,
                universal_newlines=True)
        except CalledProcessError as e:
            logging.error("Container build for {} failed: Exit {}, {}".format(
                ctr_tag, e.returncode, e.output))
        else:
            return build_output

    def _container_execute(self, ctr_tag, ctr_name, cmd=None, mountpoints=None, rm=True):
        # Running docker is available to root or users in the group `docker` only.
        # To not run the complete web application with such elevated privigeles, we
        # use `sudo` to switch to group `docker` (the user remains the same) only
        # for this particular action.
        #
        # In order for this to work, the administrator must whitelist the command and
        # the options used here in /etc/sudoers.
        #
        # Whitelisting ensures several things:
        #   - only the user running gunicorn can call docker this way
        #   - it is not possible to call docker in another fashion, e.g. specifying
        #     other options or other Docker images
        popen_args = ['sudo', '-g', 'docker', 'docker', 'run']
        # Remove container after execution?
        if rm:
            popen_args.extend(['--rm=true'])
        # Spawn tty
        popen_args.append('--tty')
        # Container name
        popen_args.extend(['--name', ctr_name])
        # Add mountpoints: {host: container} -> -v=host:container
        if mountpoints:
            popen_args.extend(['-v={}:{}'.format(k, v) for k, v in mountpoints.items()])
        # Attach to stdout
        popen_args.extend(['-a', 'STDOUT'])
        # Add the image that is to be run
        popen_args.extend([ctr_tag])
        # Add the actual compilation and test command
        popen_args.append(cmd) if cmd else logging.debug("No slug given to docker run")
        logging.debug("Container execution arguments: {}".format(popen_args))
        # Execute container
        compiler_error = False
        try:
            # Runs smoothly if all tests are successful
            cont_output = check_output(
                popen_args,
                stderr=STDOUT,
                timeout=settings.CHECKER['Timeouts'].get('container_execution'))
        except CalledProcessError as e:
            cont_output = e.output
            if e.returncode == 42:
                logging.debug("Caught compiler error for " + ctr_name)
                # Fires if compiler error occurred
                compiler_error = True
        except TimeoutExpired as e:
            cont_output = "Your code was too slow and timed out!"
            logging.error("Execution of container {} timed out: {}".format(
                ctr_name, e.timeout
            ))
            self._kill_and_remove(ctr_name, rm)

        return (cont_output, compiler_error)

    def _kill_and_remove(self, ctr_name, rm):
        try:
            check_output(
                ['docker', 'kill', ctr_name],
                timeout=settings.CHECKER['Timeouts'].get('container_kill'))
            if rm:
                check_output(
                    ['docker', 'rm', '-f', ctr_name],
                    timeout=settings.CHECKER['Timeouts'].get('container_remove'))
        except CalledProcessError as e:
            logging.error("Kill and remove of container {} failed: Exit {}, {}".format(
                ctr_name, e.returncode, e.output
            ))
        except TimeoutExpired as e:
            logging.error("Kill and remove of container {} timed out: {}".format(
                ctr_name, e.timeout
            ))

    def _parse_result(self, result, compiler_error=False):
        # TODO: Add return code to logic
        logging.debug("Parse result call")
        passed = True and not compiler_error
        time = 0.0
        if not result:
            logging.debug("_parse_result got an empty result")
            result = "For some reason I didn't get anything.. What are you doing?"
        elif compiler_error:
            # Also stick with the default values to just display result
            logging.debug("_parse_result registered a compiler error and can't parse the reports")
        else:
            result = result.decode()
            logging.debug("Got result: " + result)
            p = ET.XMLParser()
            p.feed('<root>')  # Introduce fake root element to parse multiple XML documents
            for xml_content in result.split('<?xml version="1.0" encoding="UTF-8"?>'):
                p.feed(xml_content.strip())
            p.feed('</root>')
            root = p.close()

            times = []
            for testsuite in root:
                times.append(testsuite.attrib.get('time'))
                if int(testsuite.attrib.get('failures')) != 0 \
                   or int(testsuite.attrib.get('errors')) != 0:
                    passed = False
            time = round(sum([float(x) for x in times]), 2)

        cr = CheckerResult(
            solution=self.solution,
            stdout=result,
            time_taken=time,
            passed=passed)
        cr.save()

        if passed:
            ts = TaskSolution.objects.get(pk=self.solution.pk)
            ts.passed = True
            ts.save()
