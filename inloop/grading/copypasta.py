"""
Plagiarism detection support using JPlag.
"""

import re
import subprocess
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from typing import Dict, Iterable, Optional, Set

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import QuerySet

from huey.api import Result
from huey.contrib.djhuey import db_task

from inloop.grading.models import save_plagiarism_set
from inloop.solutions.models import Solution
from inloop.tasks.models import Task

LINE_REGEX = re.compile(r"Comparing (.*?)-(.*?): (\d+\.\d+)")


@db_task()
def jplag_check_async(users: QuerySet, tasks: QuerySet) -> Result:
    """
    Submit a job to check solutions using the jplag_check function.

    This function returns immediately and is supposed to be called from inside
    view code. The actual JPlag invocation happens in a background worker process
    that will wait for JPlag to complete.

    The given queryset arguments will be serialized (pickled) before they are sent
    to the background queue.

    The results of the check will be available in the PlagiarismTest model.

    Args:
        users: A User queryset.
        tasks: A Task queryset.

    Returns:
        A huey Result object.
    """
    jplag_check(users, tasks)


def jplag_check(
    users: Iterable[User],
    tasks: Iterable[Task],
    min_similarity: Optional[int] = None,
    result_dir: Optional[Path] = None,
) -> Set[Solution]:
    """
    Check solutions of the given users for the given tasks with JPlag.

    Args:
        users: A User iterable (e.g., queryset).
        tasks: A Task iterable (e.g., queryset).
        min_similarity: Minimum solution similarity after which two solutions
            shall be regarded as plagiarism (optional).
        result_dir: Directory where JPlag HTML files shall be saved to (optional).
            The given directory must not already exist.

    Returns:
        A set containing the solutions that have been identified as plagiarism.
    """
    if min_similarity is None:
        min_similarity = settings.JPLAG_DEFAULT_SIMILARITY
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir)
        plagiarism_set = set()
        for task in tasks:
            plagiarism_set.update(jplag_check_task(users, task, min_similarity, path))
        save_plagiarism_set(plagiarism_set, str(path))
        if result_dir:
            copytree(src=path, dst=result_dir)
        return plagiarism_set


def jplag_check_task(
    users: Iterable[User],
    task: Task,
    min_similarity: int,
    result_path: Path,
) -> Set[Solution]:
    """
    Check solutions of the given users for the given single task with JPlag.

    Args:
        users: A User queryset.
        task: A Task object.
        min_similarity: Minimum solution similarity after which two solutions
            shall be regarded as plagiarism.
        result_path: Directory where JPlag HTML files shall be saved to.

    Returns:
        A set containing the solutions that have been identified as plagiarism.
    """
    with TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)
        last_solutions = get_last_solutions(users, task)
        if len(last_solutions) < 2:
            return set()
        prepare_directories(root_path, last_solutions)
        output = exec_jplag(min_similarity, root_path, result_path.joinpath(task.slug))
    return parse_output(output, min_similarity, last_solutions)


def get_last_solutions(users: Iterable[User], task: Task) -> Dict[str, Solution]:
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


def prepare_directories(root_path: Path, last_solutions: Dict[str, Solution]) -> None:
    """
    Copy the given solutions to root_path, using the folder structure expected by JPlag.

    The expected folder structure, for one task, will look like this:

        root_path/
            user-1/
                File1.java
                File2.java
            user-2/
                File1.java
                File2.java
    """
    for username, last_solution in last_solutions.items():
        copytree(src=last_solution.path, dst=root_path.joinpath(username))


def parse_output(
    output: str,
    min_similarity: int,
    last_solutions: Dict[str, Solution],
) -> Set[Solution]:
    """
    Extract plagiarism check results from the given JPlag command line output.

    Returns:
         A set containing the solutions that have been identified as plagiarism.
    """
    plagiarism_set = set()
    for match in LINE_REGEX.finditer(output):
        username1, username2, similarity = match.groups()
        similarity = float(similarity)
        if similarity >= min_similarity:
            plagiarism_set.add(last_solutions[username1])
            plagiarism_set.add(last_solutions[username2])
    return plagiarism_set


def exec_jplag(min_similarity: int, root_path: Path, result_path: Path) -> str:
    """
    Execute the JPlag Java program with the given parameters and return its output.
    """
    args = ["java", "-cp", settings.JPLAG_JAR_PATH, "jplag.JPlag"]
    args.append("-vl")
    args.extend(["-l", "java19"])
    args.extend(["-m", f"{min_similarity}%"])
    args.extend(["-r", f"{result_path}"])
    args.append(f"{root_path}")
    return subprocess.check_output(args, stderr=subprocess.DEVNULL, universal_newlines=True)
