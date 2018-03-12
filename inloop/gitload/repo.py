import os
import subprocess
from contextlib import suppress
from pathlib import Path


class Repository:
    def __init__(self, path):
        if not path:
            raise ValueError("path must not be empty")
        _path = Path(path)
        if not _path.is_absolute():
            raise ValueError("path must be absolute")
        self._path = _path

    @property
    def path(self):
        return self._path

    @property
    def path_s(self):
        return str(self._path)

    def find_files(self, glob_pattern):
        return self._path.glob(glob_pattern)

    def call_make(self, timeout=30):
        subprocess.check_call(["make"], cwd=self.path_s, timeout=timeout)

    def synchronize(self):
        pass

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.path_s)


_GIT_ENVIRON = os.environ.copy()
_GIT_ENVIRON["GIT_SSH_COMMAND"] = "ssh -F/dev/null -oBatchMode=yes -oStrictHostKeyChecking=no"


class GitRepository(Repository):
    def __init__(self, path, *, url, branch, timeout=30):
        super().__init__(path)
        if not url:
            raise ValueError("url must not be empty")
        if not branch:
            raise ValueError("branch must not be empty")
        self.url = url
        self.branch = branch
        self.timeout = timeout

    def update(self):
        self.git("remote", "set-url", "origin", self.url)
        self.git("fetch", "--quiet", "--depth=1", "origin")
        self.git("stash", "-u")
        self.git("reset", "--hard", "origin/%s" % self.branch)

    def initialize(self):
        with suppress(FileExistsError):
            self.path.mkdir(parents=True)
        self.git("clone", "--quiet", "--depth=1", "--branch", self.branch, self.url, ".")

    def git(self, *args):
        subprocess.check_call(["git"] + list(args), cwd=self.path_s, env=_GIT_ENVIRON,
                              stdout=subprocess.DEVNULL, timeout=self.timeout)

    def synchronize(self):
        if self.path.joinpath(".git").is_dir():
            self.update()
        else:
            self.initialize()
