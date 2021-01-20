"""
Classes dealing with task repositories and their synchronization.
"""

import os
import subprocess
from pathlib import Path
from typing import Any, Iterator, Optional, Union


class Repository:
    """Local task repository that does not perform synchronization."""

    def __init__(self, path: Union[str, Path]) -> None:
        """
        Create a repository with the given absolute directory path, which is allowed
        to not exist yet on the file system.
        """
        if not path:
            raise ValueError("path must not be empty")
        _path = Path(path)
        if not _path.is_absolute():
            raise ValueError("path must be absolute")
        self._path = _path

    @property
    def path(self) -> Path:
        """Return the path of this repository as a pathlib.Path object."""
        return self._path

    @property
    def path_s(self) -> str:
        """Return the path of this repository as a string."""
        return str(self._path)

    def find_files(self, glob_pattern: str) -> Iterator[Any]:
        """Yield all existing files in this repository which match the given pattern."""
        return self._path.glob(glob_pattern)

    def call_make(self, timeout: int = 300) -> None:
        """Call the `make` command in this repository's directory."""
        subprocess.check_call(["make", "--silent"], cwd=self.path_s, timeout=timeout)

    def synchronize(self) -> None:
        """Synchronize files with a remote source (optional)."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.path_s!r})"


_GIT_ENVIRON = os.environ.copy()
_GIT_ENVIRON["GIT_SSH_COMMAND"] = "ssh -F/dev/null -oBatchMode=yes -oStrictHostKeyChecking=no"


class GitRepository(Repository):
    """Local task repository that can be synchronized with a remote git repository."""

    def __init__(
        self, path: Union[str, Path], *, url: str, branch: str, timeout: Optional[int] = 30
    ) -> None:
        """
        Create a repository that can be synchronized with the given git url and branch,
        which must be passed as keyword arguments. The path must be absolute and may
        point to a directory that already contains an initialized git clone. Otherwise,
        it will be created during the first synchronization. The timeout specifies the
        maximum allowed runtime for the git subprocesses spawned by this class.
        """
        super().__init__(path)
        if not url:
            raise ValueError("url must not be empty")
        if not branch:
            raise ValueError("branch must not be empty")
        self.url = url
        self.branch = branch
        self.timeout = timeout

    def update(self) -> None:
        """
        Perform the equivalent of a `git pull` in this git clone, which must already be
        initialized, using a failure-resistant strategy (currently fetch + hard reset).
        """
        self.git("remote", "set-url", "origin", self.url)
        self.git("fetch", "--quiet", "--depth=1", "origin", "+refs/heads/*:refs/remotes/origin/*")
        self.git("stash", "-u")
        self.git("reset", "--hard", f"origin/{self.branch}")

    def initialize(self) -> None:
        """Initialize the git clone for this repository."""
        self.path.mkdir(parents=True, exist_ok=True)
        self.git("clone", "--quiet", "--depth=1", "--branch", self.branch, self.url, ".")

    def git(self, *args: str) -> None:
        """Perform given `git` subcommand (and arguments) in this git clone."""
        subprocess.check_call(
            ["git"] + list(args),
            cwd=self.path_s,
            env=_GIT_ENVIRON,
            stdout=subprocess.DEVNULL,
            timeout=self.timeout,
        )

    def synchronize(self) -> None:
        """Synchronize files with the remote git repository."""
        if self.path.joinpath(".git").is_dir():
            self.update()
        else:
            self.initialize()
