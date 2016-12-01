from django.conf import settings

from huey.contrib.djhuey import db_task

from inloop.solutions.models import Solution
from inloop.testrunner.runner import DockerTestRunner


@db_task()
def check_solution(solution_id):
    """
    Huey job which calls Solution.do_check() for the Solution specified
    by solution_id.

    This function will not block, instead it submits the job to the queue
    and returns an AsyncData object immediately.

    Blocking behavior can be achieved by calling check_solution.call_local(),
    which circumvents the huey queue.

    The job's return value will be the id of the created TestResult.
    """
    #
    # model ids are used here since parameters and return values of huey
    # jobs have to be simple types (e.g., int)
    #
    solution = Solution.objects.get(pk=solution_id)
    checker = DockerTestRunner(settings.CHECKER, settings.DOCKER_IMAGE)
    result = solution.do_check(checker)
    return result.id
