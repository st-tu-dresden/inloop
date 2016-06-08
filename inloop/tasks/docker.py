import logging
import uuid
import xml.etree.ElementTree as ET
from subprocess import STDOUT, CalledProcessError, TimeoutExpired, check_output

from django.conf import settings

from inloop.tasks.models import CheckerResult, TaskSolution


# TODO: remove coupling to django and our models
class Checker:
    def __init__(self, solution):
        self.solution = solution
        self.solution_path = self.solution.solution_path()

    def start(self):
        logging.debug("Checker start call")
        ctr_name = str(uuid.uuid4())
        # self._container_build(ctr_tag='docker-test')
        result, ce = self._container_execute(
            ctr_tag=settings.CHECKER['Container'].get('container_tag'),
            ctr_name=ctr_name,
            cmd=self.solution.task.name,
            mountpoints={
                self.solution_path: settings.CHECKER['Container'].get('solution_path')
            })
        self._parse_result(result, ce)

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
        popen_args = ['docker', 'run', '--rm', '--attach=STDOUT', '--name={}'.format(ctr_name)]

        if mountpoints:
            popen_args.extend(['--volume={}:{}'.format(k, v) for k, v in mountpoints.items()])

        popen_args.append(ctr_tag)
        popen_args.append(cmd) if cmd else logging.debug("No slug given to docker run")

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
        if settings.CHECKER.get('USE_SUDO'):
            popen_args = ['sudo', '-g', 'docker'] + popen_args

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
