from typing import Any, Dict, Optional, Union

from ..common.decorators import classproperty
from ..models import DataModel
from ..models.req import ExecReq
from .component_root import ComponentRoot


class ComponentGeneric(ComponentRoot):
    @classproperty
    def input(cls):
        return DataModel

    @classproperty
    def output(cls):
        return DataModel

    def execute(
        self,
        input_data: Union[DataModel, Dict[str, Any]],
        exec_req: Optional[ExecReq] = None,
        **kwargs: Optional[Dict[str, Any]],
    ) -> DataModel:
        raise NotImplementedError
