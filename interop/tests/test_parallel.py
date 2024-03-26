import pytest

from interop.utils.parallel import starmap_async


def foo(*args, **kwargs):  # pragma: no cover
    return 0


@pytest.mark.parametrize("debug", [True, False])
def test_starmap_async(debug):
    output = starmap_async(
        func=lambda: 0, func_input=[], num_workers=2, arg1="arg1", arg2="arg2", debug=debug
    )  # pragma: no cover
    assert len(output) == 0

    ndata = 10
    output = starmap_async(
        func=foo,
        func_input=[(1,) for _ in range(ndata)],
        num_workers=2,
        arg1="arg1",
        arg2="arg2",
        debug=debug,
    )
    assert len(output) == ndata
