import os
from contextlib import contextmanager
from subprocess import Popen, PIPE
from threading import Timer


@contextmanager
def timelimit(timeout, function):
    """Context manager which executes function after timeout seconds."""
    t = Timer(timeout, function)
    t.start()
    try:
        yield
    finally:
        t.cancel()


@contextmanager
def chdir(path):
    oldpath = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(oldpath)


class BasicRunner:
    """Simple runner that supports a timeout and uses a clean environment."""
    def __init__(self):
        self.timeout = 5
        self.cwd = None

    def run(self, args):
        proc = Popen(args, env={}, cwd=self.cwd, stdout=PIPE,
                     stderr=PIPE, universal_newlines=True)
        with timelimit(self.timeout, lambda: proc.kill()):
            outs, errs = proc.communicate()
        # XXX: raise exception? (means we lose the output)
        return (outs, errs, proc.returncode)
