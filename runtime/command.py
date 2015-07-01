from contextlib import contextmanager
from subprocess import Popen
from threading import Timer


def killer(proc):
    "Return a function that calls proc.kill()"
    def _func():
        proc.kill()
    return _func


@contextmanager
def timelimit(timeout, function):
    "Context manager which executes function after a timeout seconds"
    t = Timer(timeout, function)
    t.start()
    yield
    t.cancel()


class BasicRunner:
    """
    Runs Popen objects with timeouts, in a sane environment and optionally a tmpdir.
    """
    def __init__(self, args, timeout=15, cwd=None):
        self.args = args
        self.timeout = timeout
        self.cwd = cwd

    def run(self):
        proc = Popen(self.args, env={}, cwd=self.cwd)
        with timelimit(self.timeout, killer(proc)):
            # Note: in Python > 3.3, communicate() also supports a timeout parameter
            stdout, stderr = proc.communicate()
        return (stdout, stderr, proc.returncode)


class DockerRunner(BasicRunner):
    """
    This will run commands inside a docker container ... some time in the future.
    """
    pass
