#!/usr/bin/env python3
"""Run the INLOOP test suite with optional dynamic type checks."""
import argparse

from environ import Env

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the INLOOP test suite.")
    parser.add_argument(
        "--with-typeguard", action="store_true", help="run with dynamic type checks"
    )
    parser.add_argument(
        "test_args", nargs="*", help="arguments to pass to ./manage.py test (separate with --)"
    )
    options = parser.parse_args()

    # Because read_env(…) uses dict.setdefault(…), we can share most
    # variables between the environment files. Variables in earlier
    # loaded env files take precedence.
    Env.read_env(".env_tests")
    Env.read_env(".env_development")

    if options.with_typeguard:
        from typeguard.importhook import install_import_hook

        install_import_hook("inloop")

    from django.core.management import execute_from_command_line

    execute_from_command_line(["./manage.py", "test", *options.test_args])
