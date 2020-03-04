#!/usr/bin/env python3
"""Execute Django and INLOOP management commands."""
import sys

from environ import Env

if __name__ == '__main__':
    # Because read_env(…) uses dict.setdefault(…), we can share most
    # variables between the environment files. Variables in earlier
    # loaded env files take precedence.
    if 'test' in sys.argv[:2]:
        Env.read_env('.env_tests')
    Env.read_env('.env_development')

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
