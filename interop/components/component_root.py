import abc
from typing import Any, Dict, Optional, Union

from ..common.decorators import classproperty
from ..models import DataModel, RootModel
from ..models.req import ExecReq


class ComponentRoot(RootModel, metaclass=abc.ABCMeta):
    @abc.abstractproperty
    @classproperty
    def input(cls):  # pragma: no cover
        ...

    @abc.abstractproperty
    @classproperty
    def output(cls):  # pragma: no cover
        ...

    @abc.abstractmethod
    def execute(  # pragma: no cover
        self,
        input_model: Union[DataModel, Dict[str, Any]],
        exec_req: Optional[ExecReq] = None,
        **kwargs: Optional[Dict[str, Any]],
    ) -> DataModel:
        ...

    @classmethod
    def compute(
        cls,
        input_data: Union[DataModel, Dict[str, Any]],
        exec_req: Optional[ExecReq] = None,
        **kwargs: Optional[Dict[str, Any]],
    ) -> DataModel:
        """
        This class method parses and validates input data, then it
        returns a validated output data model. Since ``exec_req`` is
        a small data object, validation is always done. In contrast,
        validation is skipped for ``input_data`` and ``output_data`` if
        the latter is a (direct) instance of cls.input or cls.output. The
        reason being validation in this case **might** create a significant
        overhead, so it's skippable.

        Parameters
        ----------
        input_data: DataModel or dict[str, any]
            Input data object that must comply with the input schema defined
            in cls.input. See :class:`DataModel`.
        exec_req: ExecReq, optional
            Execution requirement model. See :class:`ExecReq`.
        **kwargs: dict[str, any], optional
            Additional keyword args to pass to ``self.execute``.

        Returns
        -------
        output_data: DataModel
            Validated output data object

        """

        if exec_req is not None:
            # pydantic always validates exec_req
            exec_req = ExecReq.model_validate(exec_req)

        # validate input if required
        if input_data.__class__ is not cls.input:
            input_data = cls.input.model_validate(input_data)

        # instantiate class
        component = cls()

        # execute component
        output_data = component.execute(input_data, exec_req, **kwargs)

        # validate output if required
        if output_data.__class__ is not cls.output:
            output_data = cls.output.model_validate(output_data)

        return output_data
