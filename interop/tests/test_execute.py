import os

import pytest

from interop.utils import execute


@pytest.mark.parametrize(
    "command", [("ls", "-ltr", os.getcwd()), ("grep", "-r", "interop", os.getcwd())]
)
def test_noinput(command):
    success, output = execute(command=command)
    assert success
    assert output["stdout"]


@pytest.mark.skip("TBD")
def test_io(command, intput, output):
    success, output = execute(command=command)
    assert success
    assert output["stdout"]
