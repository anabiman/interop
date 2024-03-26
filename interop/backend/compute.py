"""
For running programs, you need to define the EXEC variable below.
"""

from typing import Final

from mds_dev import execute

EXEC: Final = "path/to/executable"  # e.g. "/opt/soft/COMSOL"


def compute_from_disk(**kwargs):
    return execute(EXEC, **kwargs)


def compute_from_mem(**kwargs):
    return ...
