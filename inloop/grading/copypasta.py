"""
Plagiarism detection support using jPlag.

Assumes that the jPlag JAR archive is on the CLASSPATH.
"""
import re
import subprocess
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory

from django.conf import settings

from huey.contrib.djhuey import db_task

from inloop.grading.models import save_plagiarism_set
from inloop.solutions.models import Solution

LINE_REGEX = re.compile(r"Comparing (.*?)-(.*?): (\d+\.\d+)")


@db_task()
def jplag_check_async(users, tasks, min_similarity=settings.JPLAG_SIMILARITY, result_dir=None):
    jplag_check(users, tasks, min_similarity, result_dir)


def jplag_check(users, tasks, min_similarity=settings.JPLAG_SIMILARITY, result_dir=None):
    """
    Check tasks with JPlag.

    Returns:
        A set containing the solutions that have been identified as plagiarism.
    """
    with TemporaryDirectory() as path:
        path = Path(path if not result_dir else result_dir)
        plagiarism_set = set()
        for task in tasks:
            plagiarism_set.update(jplag_check_task(users, task, min_similarity, path))
        save_plagiarism_set(plagiarism_set, str(path))
        return plagiarism_set


def jplag_check_task(users, task, min_similarity, result_path):
    """
    Check a given task for given users, comparing their solutions
    and triggering a detected plagiarism when two solutions
    match to a specified similarity. Store JPlag output in
    a specified output directory.
    """
    with TemporaryDirectory() as root_path:
        root_path = Path(root_path)
        last_solutions = get_last_solutions(users, task)
        prepare_directories(root_path, last_solutions)
        output = exec_jplag(min_similarity, root_path, result_path.joinpath(task.slug))
    return parse_output(output, min_similarity, last_solutions)


def get_last_solutions(users, task):
    """
    Get the last valid solution of the given users for a given task.
    """
    last_solutions = {}
    for user in users:
        last_solution = Solution.objects.filter(author=user, task=task, passed=True).last()
        if last_solution is not None:
            # escape hyphens in usernames with an unused (since
            # disallowed) character, otherwise the usernames cannot
            # be extracted from the jplag output
            last_solutions[user.username.replace("-", "$")] = last_solution
    return last_solutions


def prepare_directories(root_path, last_solutions):
    for username, last_solution in last_solutions.items():
        copytree(str(last_solution.path), str(root_path.joinpath(username)))


def parse_output(output, min_similarity, last_solutions):
    """
    Parse JPlag output.
    """
    plagiarism_set = set()
    for match in LINE_REGEX.finditer(output):
        username1, username2, similarity = match.groups()
        similarity = float(similarity)
        if similarity >= min_similarity:
            plagiarism_set.add(last_solutions[username1])
            plagiarism_set.add(last_solutions[username2])
    return plagiarism_set


def exec_jplag(min_similarity, root_path, result_path):
    """
    Execute the JPlag Java program with the given parameters and return its output.
    """
    args = ["java"]
    args += ["-cp", settings.JPLAG_JAR_PATH]
    args += ["jplag.JPlag"]
    args += ["-vl"]
    args += ["-l", "java17"]
    args += ["-m", str(min_similarity)]
    args += ["-r", str(result_path)]
    args += [str(root_path)]
    return subprocess.check_output(args, stderr=subprocess.DEVNULL, universal_newlines=True)
