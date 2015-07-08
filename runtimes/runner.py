from contextlib import contextmanager
from subprocess import Popen
from threading import Timer


@contextmanager
def timelimit(timeout, function):
    """Context manager which executes function after timeout seconds."""
    t = Timer(timeout, function)
    t.start()
    yield
    t.cancel()


class TimeoutExpired(Exception):
    pass


class BasicRunner:
    """Simple runner that supports a timeout and uses a clean environment."""
    def __init__(self, timeout=5, cwd=None):
        self.timeout = timeout
        self.cwd = cwd

    def run(self, args):
        proc = Popen(args, env={}, cwd=self.cwd)
        with timelimit(self.timeout, lambda: proc.kill()):
            outs, errs = proc.communicate()
        # XXX: raise exception? (means we lose the output)
        return (outs, errs, proc.returncode)
