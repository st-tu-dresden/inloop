import os
import subprocess
from pathlib import Path


class Repository:
    def __init__(self, path):
        if not path:
            raise ValueError("path must not be empty")
        self._path = Path(path).resolve()

    @property
    def path(self):
        return self._path

    def find_files(self, glob_pattern):
        return self._path.glob(glob_pattern)

    def call_make(self, timeout=30):
        subprocess.check_call(["make"], cwd=str(self.path), timeout=timeout)

    def synchronize(self):
        pass

    def __repr__(self):
        return "Repository(%s)" % self.path


class GitRepository(Repository):
    def __init__(self, path, url, branch, timeout=30):
        super().__init__(path)
        if not url:
            raise ValueError("url must not be empty")
        if not branch:
            raise ValueError("branch must not be empty")
        self.url = url
        self.branch = branch
        self.timeout = timeout
        self.environ = os.environ.copy()
        self.environ["GIT_SSH_COMMAND"] = " ".join([
            "ssh",
            "-F/dev/null",
            "-oBatchMode=yes",
            "-oStrictHostKeyChecking=no"
        ])

    def update(self):
        self.git("remote", "set-url", "origin", self.url)
        self.git("fetch", "--quiet", "--depth=1", "origin")
        self.git("stash", "-u")
        self.git("reset", "--hard", "origin/%s" % self.branch)

    def initialize(self):
        try:
            self.path.mkdir(parents=True)
        except FileExistsError:
            pass
        self.git("clone", "--quiet", "--depth=1", "--branch", self.branch, self.url, ".")

    def git(self, *args):
        subprocess.check_call(["git"] + list(args), cwd=str(self.path), env=self.environ,
                              stdout=subprocess.DEVNULL, timeout=self.timeout)

    def synchronize(self):
        if self.path.joinpath(".git").is_dir():
            self.update()
        else:
            self.initialize()

    def __repr__(self):
        return "GitRepository(path='%s', url='%s', branch='%s')" % (
            self.path, self.url, self.branch
        )
