import numpy

from interop.utils.misc import check_symmetry, get_call_method


def test_symmetry():
    mat = numpy.random.rand(3, 3)
    assert not check_symmetry(mat)
    symm = 0.5 * (mat + mat.T)
    assert check_symmetry(symm)


def test_call_method():
    assert get_call_method()
