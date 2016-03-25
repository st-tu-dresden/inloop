#!/usr/bin/env python
import os
import sys
import warnings

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inloop.settings.development")
    warnings.simplefilter("default")
    warnings.filterwarnings("ignore", "the imp module is deprecated",
                            PendingDeprecationWarning, "imp")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
