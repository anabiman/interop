from typing import Any, Dict, Final, Optional, Set, Union

from pydantic import BaseModel

from ..utils import serialization

# Addresses the draft issue https://github.com/samuelcolvin/pydantic/issues/1478
schema_draft = "http://json-schema.org/draft-07/schema#"


class RootModel(BaseModel):
    """
    A mutable Pydantic BaseModel class with extended serialization support.
    This is the most fundamental class that superclasses every data model and
    interoperable component.

    """

    class ConfigDict:
        frozen: Final[bool] = False
        extra: str = "allow"
        arbitrary_types_allowed: bool = True

        def json_schema_extra(schema, model):
            schema["$schema"] = schema_draft

    def serialize(
        self,
        encoding: str,
        *,
        include: Optional[Set[str]] = None,
        exclude: Optional[Set[str]] = None,
        exclude_unset: Optional[bool] = None,
        exclude_defaults: Optional[bool] = None,
        exclude_none: Optional[bool] = None,
        **kwargs: Optional[Dict[str, Any]],
    ) -> Union[bytes, str]:
        """
        Generates a serialized representation of the model. Must support YAML.

        """

        pydantic_kwargs = {}
        if include:
            pydantic_kwargs["include"] = include
        if exclude:
            pydantic_kwargs["exclude"] = exclude
        if exclude_unset:
            pydantic_kwargs["exclude_unset"] = exclude_unset
        if exclude_defaults:
            pydantic_kwargs["exclude_defaults"] = exclude_defaults
        if exclude_none:
            pydantic_kwargs["exclude_none"] = exclude_none

        data = self.model_dump(**pydantic_kwargs)

        if encoding == "js":
            encoding = "json"
        elif encoding == "yml":
            encoding = "yaml"

        return serialization.serialize(data, encoding=encoding, **kwargs)
