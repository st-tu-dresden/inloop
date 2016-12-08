#!/usr/bin/env python3
import sys

from environ import Env

if __name__ == "__main__":
    if "test" in sys.argv[:2]:
        Env.read_env("tests/.env")
    else:
        Env.read_env(".env")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
