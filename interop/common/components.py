import enum
import inspect
from typing import Callable, Tuple

from ..components import ComponentGeneric, ComponentRay
from ..models import DataModel


class ComponentTypes(enum.Enum):
    generic = ComponentGeneric
    ray = ComponentRay
    default = ComponentRay


def get_models(function: Callable) -> Tuple[DataModel, DataModel]:
    """
    Returns annotations for the following function signature:

    def function(
        input_model: DataModel,
    ) -> output_model:

    Parameters
    ----------
    function: Callable
        Annotated function

    Returns
    -------
    Tuple[DataModel, DataModel]
        The annotated input and output data models

    """

    sign = inspect.signature(function)
    inspect_input = sign.parameters.get("input_model")
    input_model = None if inspect_input is None else inspect_input.annotation
    input_model = None if input_model is inspect._empty else input_model
    output_model = None if sign.return_annotation is inspect._empty else sign.return_annotation
    return input_model, output_model
