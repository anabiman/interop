"""
Provides serialization routines.
Adopted from https://github.com/MolSSI/cmselemental
"""

import json
from typing import Any, Dict, Optional, Union

import numpy
from pydantic.json import pydantic_encoder


class JSONArrayEncoder(json.JSONEncoder):  # pragma: no cover
    def default(self, obj: Any) -> Any:
        try:
            return pydantic_encoder(obj)
        except TypeError:
            pass

        if isinstance(obj, numpy.ndarray):
            if obj.shape:
                return obj.ravel().tolist()
            else:
                return obj.tolist()

        return json.JSONEncoder.default(self, obj)


def json_dumps(data: Any, **kwargs: Optional[Dict[str, Any]]) -> str:
    """
    Safe serialization of a Python dictionary to JSON string representation
    using all known encoders.

    Parameters
    ----------
    data : Any
        A encodable python object.
    **kwargs : Optional[Dict[str, Any]], optional
        Additional keyword arguments to pass to the constructor

    Returns
    -------
    str
        A JSON representation of the data.

    """

    return json.dumps(data, cls=JSONArrayEncoder, **kwargs)


def serialize(data: Any, encoding: str, **kwargs: Optional[Dict[str, Any]]) -> Union[str, bytes]:
    """
    Encoding Python objects using the provided encoder.

    Parameters
    ----------
    data : Any
        A encodable python object.
    encoding : str
        The type of encoding to perform: {'json', 'json-ext', 'yaml', 'msgpack-ext'}
    **kwargs : Optional[Dict[str, Any]], optional
        Additional keyword arguments to pass to the constructors.

    Returns
    -------
    Union[str, bytes]
        A serialized representation of the data.

    """
    if encoding.lower() == "json":
        return json_dumps(data, **kwargs)
    else:
        raise NotImplementedError(f"Encoding format {encoding} not yet supported.")
