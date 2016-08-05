#!/usr/bin/env python
import os
import sys

from environ import Env

if __name__ == "__main__":
    Env.read_env()

    if sys.argv[1] == "shell":
        sys.argv[1] = "shell_plus"
    elif "test" in sys.argv:
        os.environ["DJANGO_SETTINGS_MODULE"] = "tests.settings"

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
