#!/usr/bin/env python3
"""Execute Django and INLOOP management commands."""
import sys

from environ import Env

if __name__ == "__main__":
    if "test" in sys.argv[:2]:
        sys.exit("Error: use ./runtests.py instead of ./manage.py test")
    Env.read_env(".env_development")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
