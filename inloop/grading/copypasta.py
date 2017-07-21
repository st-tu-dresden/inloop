"""
Plagiarism detection support using jPlag.

Assumes that the jPlag JAR archive is on the CLASSPATH.
"""

from pathlib import Path
from shutil import copytree
from subprocess import check_call
from tempfile import TemporaryDirectory

from inloop.solutions.models import Solution


def jplag_check(users, tasks, similarity, result_dir):
    result_path = Path(result_dir)
    for task in tasks:
        with TemporaryDirectory() as tmpdir:
            check_task(users, task, similarity, result_path, Path(tmpdir))


def check_task(users, task, similarity, result_path, root_path):
    for user in users:
        last_solution = Solution.objects.filter(author=user, task=task).last()
        if last_solution is not None:
            copytree(str(last_solution.path), str(root_path.joinpath(user.username)))
    exec_jplag(similarity, root_path, result_path.joinpath(task.slug))


def exec_jplag(similarity, root_path, result_path):
    args = "java jplag.JPlag -vq -l java17".split()
    args += ["-m", str(similarity)]
    args += ["-r", str(result_path)]
    args += [str(root_path)]
    check_call(args)
