from typing import Any, Dict, Optional, Union

import numpy
from pydantic import PositiveInt

from ..common.decorators import classproperty
from ..utils.data import Field
from .root import RootModel


class DataModel(RootModel):
    """
    Immutable class with internal validation. Serves as a base class for all
    data classes.

    """

    schema_name: str = Field(
        "unknown",
        description="Name specification this model conforms to.",
    )
    schema_version: PositiveInt = Field(
        1,
        description="Version specification this model conforms to.",
    )

    class ConfigDict(RootModel.ConfigDict):
        frozen: bool = True
        extra: str = "forbid"
        json_encoders: Dict[str, Any] = {
            numpy.ndarray: lambda v: v.flatten().tolist(),
        }  # pragma: no cover

    def __init_subclass__(cls, **kwargs: Optional[Dict[str, Any]]) -> None:
        super().__init_subclass__(**kwargs)

    def __repr__(self) -> str:
        return f'{self.__repr_name__()}({self.__repr_str__(", ")})'

    def __str__(self) -> str:
        return f'{self.__repr_name__()}({self.__repr_str__(", ")})'

    @classproperty
    def default_schema_name(cls) -> Union[str, None]:
        """Returns default schema name if found."""
        try:
            return cls.schema()["properties"]["schema_name"]["default"]
        except KeyError:
            return None

    def json(self, **kwargs):
        # Alias JSON here from BaseModel to reflect dict changes
        return self.serialize("json", **kwargs)

    def yaml(self, **kwargs):
        raise NotImplementedError("YAML serialization not yet supported.")
