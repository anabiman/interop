"""
Creates a ``__version__`` variable with the proper version.

This file is automatically generated by
https://dev.azure.com/dcimds/MDS_Demo_Platform/_git/backend-python-cookiecutter-template
Do not edit! Update the template instead.
"""
try:
    from importlib import metadata
except ImportError:  # pragma: no cover
    # For Py37 and below, use the import_metadata backport
    import importlib_metadata as metadata

__version__ = metadata.version("interop")
