import logging
import re
import string
import xml.etree.ElementTree as ET
from os.path import dirname, join
from random import SystemRandom
from subprocess import STDOUT, CalledProcessError, TimeoutExpired, check_output

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from inloop.accounts.models import UserProfile
from inloop.gh_import.utils import parse_date


def make_slug(value):
    """Extended slugify() that also removes '(...)' from strings.

    Example:
    >>> make_slug("Some Task III (winter term 2010/2011)")
    'some-task-iii'
    """
    return slugify(re.sub(r'\([^\)]+\)', '', value))


def get_upload_path(instance, filename):
    path = join(
        'solutions',
        instance.solution.author.username,
        instance.solution.task.slug,
        timezone.now().strftime('%Y/%m/%d/%H_%M_') + str(instance.solution.id),
        filename)
    return path


class TaskCategoryManager(models.Manager):
    def get_or_create(self, name):
        """Retrieve TaskCategory if it exists, create it otherwise."""
        try:
            return self.get(name=name)
        except ObjectDoesNotExist:
            return self.create(name=name, short_id=slugify(name))


class TaskCategory(models.Model):
    short_id = models.CharField(
        unique=True,
        max_length=50,
        help_text='Short ID for URLs')
    name = models.CharField(
        unique=True,
        max_length=50,
        help_text='Category Name')
    image = models.ImageField(null=True, upload_to='images/category_thumbs/')
    objects = TaskCategoryManager()

    def save(self, *args, **kwargs):
        self.short_id = slugify(self.name)
        super(TaskCategory, self).save(*args, **kwargs)

    def get_tuple(self):
        return (self.short_id, self.name)

    def completed_tasks_for_user(self, user):
        '''Returns the tasks a user has already solved.'''
        return Task.objects.filter(
            tasksolution__author=user,
            tasksolution__passed=True,
            category=self
        )

    def get_tasks(self):
        '''Returns a queryset of this category's task that have already been
        published'''
        return Task.objects.filter(
            category=self,
            publication_date__lt=timezone.now())

    def __str__(self):
        return self.name


class MissingTaskMetadata(Exception):
    pass


class TaskManager(models.Manager):
    meta_required = ['title', 'category', 'pubdate']

    def get_or_create_json(self, json, name):
        author = UserProfile.get_system_user()
        try:
            task = self.get(name=name)
        except ObjectDoesNotExist:
            task = Task(name=name, author=author)
        return self._update_task(task, json)

    def _update_task(self, task, json):
        self._validate(json)
        task.title = json['title']
        task.slug = make_slug(task.title)
        task.category = TaskCategory.objects.get_or_create(json['category'])
        task.publication_date = parse_date(json['pubdate'])
        return task

    def _validate(self, json):
        missing = []
        for meta_key in self.meta_required:
            if meta_key not in json.keys():
                missing.append(meta_key)
        if missing:
            raise MissingTaskMetadata(missing)


class Task(models.Model):
    """Represents the tasks that are presented to the user to solve."""

    # Mandatory fields:
    title = models.CharField(max_length=100, help_text='Task title')
    name = models.CharField(max_length=100, help_text='Internal task name')
    slug = models.SlugField(max_length=50, unique=True, help_text='URL name')
    description = models.TextField(help_text='Task description')
    publication_date = models.DateTimeField(help_text='When should the task be published?')

    # Optional fields:
    deadline_date = models.DateTimeField(help_text='Date the task is due to', null=True)

    # Foreign keys:
    author = models.ForeignKey(UserProfile)
    category = models.ForeignKey(TaskCategory)

    objects = TaskManager()

    def is_active(self):
        """Returns True if the task is already visible to the users."""
        return timezone.now() > self.publication_date

    def task_location(self):
        return join(settings.MEDIA_ROOT, 'exercises', self.slug)

    def __str__(self):
        return self.name


class TaskSolution(models.Model):
    '''Represents the user uploaded files'''

    submission_date = models.DateTimeField(
        help_text='When was the solution submitted?')
    author = models.ForeignKey(UserProfile)
    task = models.ForeignKey(Task)
    passed = models.BooleanField(default=False)

    def solution_path(self):
        # Get arbitrary TaskSolution to get directory path
        sol_file = TaskSolutionFile.objects.filter(solution=self)[0]
        return join(dirname(sol_file.file_path()))

    def previously_solved(self):
        return TaskSolution.objects.filter(passed=True).exists()

    def __str__(self):
        return "TaskSolution(author='{}', task='{}', submitted={}, passed={})".format(
            self.author.username,
            self.task,
            self.submission_date,
            self.passed
        )


class TaskSolutionFile(models.Model):
    '''Represents a single file as part of a solution'''

    solution = models.ForeignKey(TaskSolution)
    filename = models.CharField(max_length=50)
    file = models.FileField(upload_to=get_upload_path)

    def file_path(self):
        return self.file.path

    def __str__(self):
        return "TaskSolutionFile('%s')" % self.file


class CheckerResult(models.Model):
    solution = models.ForeignKey(TaskSolution)
    result = models.TextField()
    time_taken = models.FloatField()
    passed = models.BooleanField(default=False)

    def __str__(self):
        return "CheckerResult(solution_id=%d, passed=%s)" % (self.solution.id, self.passed)


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
            for xml_content in result.split('<?xml version="1.0" encoding="UTF-8"?>\r\n'):
                p.feed(xml_content)
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
            result=result,
            time_taken=time,
            passed=passed)
        cr.save()

        if passed:
            # If previously unsolved exam task: give bonus point
            if self.solution.task.category.name in settings.BONUS_CATEGORIES \
               and not self.solution.previously_solved():
                self.solution.author.bonus_points += 1
            # Mark TaskSolution as passed
            ts = TaskSolution.objects.get(pk=self.solution.pk)
            ts.passed = True
            ts.save()
