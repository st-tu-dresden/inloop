import logging
import subprocess
import time
import uuid

from django.conf import settings
from django.db import transaction

from inloop.tasks.models import CheckerResult


LOGGER = logging.getLogger(__name__)


def maybe_sudo(args):
    # Running docker is available to root or users in the group `docker` only.
    # To not run the complete web application with such elevated privileges, we
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
    if settings.CHECKER.get('USE_SUDO'):
        args = ['sudo', '-g', 'docker'] + args

    return args


# TODO: remove coupling to django and our models
class Checker:
    def __init__(self, solution):
        self.solution = solution
        self.solution_path = self.solution.solution_path()

    def start(self):
        result = self.container_execute(
            ctr_tag=settings.CHECKER['Container'].get('container_tag'),
            ctr_name=str(uuid.uuid4()),
            cmd=self.solution.task.name,
            mountpoints={
                self.solution_path: settings.CHECKER['Container'].get('solution_path')
            }
        )
        self.parse_result(result)

    def container_execute(self, ctr_tag, ctr_name, cmd=None, mountpoints=None, rm=True):
        popen_args = ['docker', 'run', '--rm', '--name={}'.format(ctr_name)]

        if mountpoints:
            popen_args.extend(['--volume={}:{}'.format(k, v) for k, v in mountpoints.items()])

        popen_args.append(ctr_tag)
        popen_args.append(cmd) if cmd else logging.debug("No slug given to docker run")

        popen_args = maybe_sudo(popen_args)

        LOGGER.debug("Popen args: %s", popen_args)

        proc = subprocess.Popen(
            popen_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )

        start_time = time.perf_counter()

        try:
            stdout, stderr = proc.communicate(timeout=50)
            rc = proc.returncode
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            rc = -9
            subprocess.call(maybe_sudo(['docker', 'rm', '--force', ctr_name]))

        runtime = time.perf_counter() - start_time

        if rc in (125, 126, 127):
            stdout = "You've encountered an error only the admin can fix. Please try again later."
            LOGGER.error("docker failure (rc=%d): %s", rc, stderr)

        return (rc, stdout, runtime)

    def parse_result(self, result):
        rc, stdout, runtime = result
        passed = (rc == 0)

        if rc == -9:
            stdout = "Your submitted programm was too slow and has been terminated."

        with transaction.atomic():
            CheckerResult.objects.create(
                solution=self.solution,
                stdout=stdout,
                time_taken=runtime,
                passed=passed,
                return_code=rc
            )
            self.solution.passed = passed
            self.solution.save()
