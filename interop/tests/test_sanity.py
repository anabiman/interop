import sys

import interop


def test_version():
    assert interop.__version__


def test_import():
    assert "interop" in sys.modules
