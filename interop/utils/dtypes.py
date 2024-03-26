from typing import Any, Dict

import numpy
from pydantic.types import (
    DirectoryPath,
    FilePath,
    NonNegativeFloat,
    NonNegativeInt,
    PositiveFloat,
    PositiveInt,
)

__all__ = [
    "PositiveFloat",
    "NonNegativeInt",
    "NumpyArray",
    "FilePath",
    "DirectoryPath",
    "PositiveInt",
    "NonNegativeFloat",
]


# Numpy dtypes for heterogenous arrays
NUMPY_INT = "i8"
NUMPY_FLOAT = "f8"
NUMPY_UNI = "U4"


class _TypedArray(numpy.ndarray):  # pragma: no cover
    @classmethod
    def __get_validators__(cls):
        yield cls.model_validate

    @classmethod
    def validate(cls, v):
        try:
            v = numpy.asarray(v, dtype=cls._dtype)
        except ValueError:
            raise ValueError("Could not cast {} to NumPy Array!".format(v))

        return v

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        dt = cls._dtype
        if dt is int or numpy.issubdtype(dt, numpy.integer):
            items = {"type": "number", "multipleOf": 1.0}
        elif dt is float or numpy.issubdtype(dt, numpy.floating):
            items = {"type": "number"}
        elif dt is str or numpy.issubdtype(dt, numpy.string_):
            items = {"type": "string"}
        elif dt is bool or numpy.issubdtype(dt, numpy.bool_):
            items = {"type": "boolean"}
        else:  # assume array otherwise
            items = {"type": "array"}
        field_schema.update(type="array", items=items)


class _ArrayMeta(type):  # pragma: no cover
    def __getitem__(cls, dtype):
        return type("NumpyArray", (_TypedArray,), {"_dtype": dtype})


class NumpyArray(numpy.ndarray, metaclass=_ArrayMeta):
    # NumpyArray[dtype] calls metaclass.__getitem__(cls, dtype)
    # In contrast, NumpyArray.getitem(dtype) calls class.__getitem__(cls, dtype).
    # For this reason, __getitem__ is defined in _ArrayMeta. This way we can
    # define numpy array types: NumpyArray[int], etc.
    pass
