from importlib import import_module
from typing import Any, Callable, Dict, Optional, Type, Union

from ..models import DataModel
from ..models.req import ExecReq
from .component_root import ComponentRoot

try:
    import ray
    import ray.dag
except ModuleNotFoundError:
    import warnings

    ray = None
    warnings.warn("Ray unavailable. Remote compute for ComponentRay is disabled.", stacklevel=1)


def compute_remote(
    cls: Type,
    exec_req: Optional[ExecReq] = None,
) -> Callable:
    def local_compute(
        input_data: cls.input,
        exec_req: Optional[ExecReq] = None,
        **kwargs: Optional[Dict[str, Any]],
    ) -> cls.output:
        """
        Ray does not support partial functions. So this
        function creates foo = partial(cls.compute, cls=cls).
        """
        return cls.compute(input_data, exec_req, **kwargs)

    exec_req = ExecReq.model_validate(exec_req)

    remote_func = ray.remote(
        **exec_req.compute_req.model_dump(
            exclude={"schema_name", "schema_version"}, exclude_unset=True
        )
    )
    return remote_func(local_compute)


class ComponentRay(ComponentRoot):
    @classmethod
    def compute_remote(  # pragma: no cover
        cls,
        input_data: Union[DataModel, Dict[str, Any]],
        exec_req: Optional[Union[ExecReq, Dict[str, Any]]] = None,
        **kwargs: Optional[Dict[str, Any]],
    ) -> ray.ObjectRef:
        """
        Parameters
        ----------
        **kwargs: dict[str, any], optional
            Optional keyword args to pass to remote function

        """

        if ray is None:
            raise ModuleNotFoundError(
                "Ray framework not installed. Solve by installing ray-default."
            )

        if (
            not callable(getattr(cls, "_compute_remote", None)) and exec_req is None
        ):  # no need for remote compute
            raise RuntimeError(f"_compute_remote method is not available in {cls.__name__}")

        if exec_req is not None:
            exec_req = ExecReq.model_validate(exec_req)

            if exec_req.compute_req:
                cls._compute_remote.options(
                    **exec_req.compute_req.model_dump(
                        exclude={"schema_name", "schema_version"}, exclude_unset=True
                    )
                )

        return cls._compute_remote.remote(input_data, exec_req, **kwargs)

    def execute(
        self,
        input_model: Union[DataModel, Dict[str, Any]],
        exec_req: Optional[ExecReq] = None,
        **kwargs: Optional[Dict[str, Any]],
    ) -> DataModel:
        raise NotImplementedError

    @classmethod
    def _compute_remote(
        cls,
        input_data: Union[DataModel, Dict[str, Any]],
        exec_req: Optional[Union[ExecReq, Dict[str, Any]]] = None,
        **kwargs: Optional[Dict[str, Any]],
    ):
        raise NotImplementedError


class MetaComponentRay(ComponentRay):  # pragma: no cover
    @classmethod
    def _register(
        cls,
        exec_req: Optional[Union[ExecReq, Dict[str, Any]]] = None,
    ) -> Callable:
        exec_req = ExecReq.model_validate(exec_req)

        @ray.remote(
            **exec_req.compute_req.model_dump(
                exclude={"schema_name", "schema_version"}, exclude_unset=True
            )
        )
        def dynamic_comp(input_data, exec_req, module, component, **kwargs):
            # Create dynamic component from metaclass
            mod = import_module(module)
            comp = getattr(mod, component, None)
            new_comp = cls._from_meta(cls=comp)
            return new_comp.compute(input_data, exec_req, **kwargs)

        return dynamic_comp

    @classmethod
    def compute_remote(
        cls,
        input_data: Union[DataModel, Dict[str, Any]],
        exec_req: Optional[Union[ExecReq, Dict[str, Any]]] = None,
        module: str = None,
        component: str = None,
        **kwargs: Optional[Dict[str, Any]],
    ) -> ray.ObjectRef:
        return cls._register(exec_req).remote(input_data, exec_req, module, component, **kwargs)

    @classmethod
    def bind(
        cls,
        input_data: Union[DataModel, Dict[str, Any]],
        exec_req: Optional[Union[ExecReq, Dict[str, Any]]] = None,
        module: str = None,
        component: str = None,
        **kwargs: Optional[Dict[str, Any]],
    ) -> ray.dag.function_node.FunctionNode:
        return cls._register(exec_req).bind(input_data, exec_req, module, component, **kwargs)
