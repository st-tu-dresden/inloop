"""
Various utility functions.
"""


def filter_uppercase_keys(d):
    """Filters a dictionary to contain only uppercase keys."""
    return {k: v for k, v in d.items() if k.isupper()}
