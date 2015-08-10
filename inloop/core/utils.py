"""
Various utility functions.
"""
import os
from contextlib import contextmanager
from threading import Timer


def filter_uppercase_keys(d):
    """Filters a dictionary to contain only uppercase keys."""
    return {k: v for k, v in d.items() if k.isupper()}


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
def changedir(path):
    """Change to path and restore the old working directory afterwards."""
    oldpath = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(oldpath)
