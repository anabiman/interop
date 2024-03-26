import inspect
import logging
from typing import Any, Optional, Type, Union

import numpy
from pydantic import ValidationError

from interop.utils.dtypes import NUMPY_FLOAT, NumpyArray


def valid_error(cls: Type[Any], *, msg: Optional[str] = None) -> ValidationError:
    exc = TypeError(msg)
    return ValidationError(repr(exc.errors()[0]["type"]))


def check_symmetry(
    matrix: NumpyArray[numpy.dtype(NUMPY_FLOAT)],
    rtol: Optional[float] = 1e-05,
    atol: Optional[float] = 1e-08,
) -> bool:
    """
    Checks if a matrix is symmetric up to a certain tolerance.

    Parameters
    ----------
    matrix: NumpyArray[numpy.dtype(NUMPY_FLOAT)]
        Input numpy matrix (2D array).
    rtol: float, optional
        Relative tolerance.
    atol: float, optional
        Absolute tolerance.

    Returns
    -------
    bool
        True if matrix is symmetric, False otherwise.

    """
    return numpy.allclose(matrix, matrix.T, rtol=rtol, atol=atol)


def red_txt(txt):  # pragma: no cover
    return f"\033[91m{txt}\033[0m"


def init_logger(
    fname: str, name: str, level: int = logging.DEBUG
) -> logging.Logger:  # pragma: no cover
    if name is None:
        return None

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if fname is not None:
        formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s", "%m-%d-%Y %H:%M:%S"
        )
        file_handler = logging.FileHandler(f"{fname}.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


class Logger:
    def __init__(self, name: str, fname: str = None, **kwargs):
        self.logger_info = init_logger(fname, name, "INFO")
        if self.logger_info is None:
            self.logger_debug = None
        else:
            fname = "." + fname if fname else None
            self.logger_debug = init_logger(fname, "debug_" + name, "DEBUG")

    def critical(self, msg):
        self.logger_info.critical(msg)
        self.logger_debug.critical(msg)

    def error(self, msg):
        self.logger_info.error(msg)
        self.logger_debug.error(msg)

    def warning(self, msg):
        self.logger_info.warning(msg)
        self.logger_debug.warning(msg)

    def info(self, msg):
        self.logger_info.info(msg)
        self.logger_debug.info(msg)

    def debug(self, msg):
        self.logger_debug.debug(msg)

    def clear(self):
        self.logger_info.handlers.clear()
        self.logger_debug.handlers.clear()

    def __del__(self):
        self.clear()


def get_call_method() -> Union[str, None]:
    """
    Returns name of the calling method.

    Returns
    -------
    str or None
        Name of calling method or None

    Note: This is probably CPython specific.

    """
    try:
        return inspect.stack()[2][3]
    except Exception:
        return None
