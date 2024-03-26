import functools
import importlib
import inspect
import types
from typing import Any, Callable, ClassVar, Dict, Tuple, Type, Union, get_type_hints

from ..common.components import ComponentTypes
from ..components import ComponentRay, ComponentRoot, MetaComponentRay
from ..components.component_ray import compute_remote
from ..models import DataModel, ExecReq


def singleton(func: Callable) -> Callable:
    def wrapper(*args, **kwargs):
        if not wrapper._has_run:
            wrapper._has_run = True
            return func(*args, **kwargs)
        else:
            raise RuntimeError(f"Function {func.__name__} cannot be called more than once!")

    wrapper._has_run = False
    return wrapper


def _comp_adapter(func_or_cls: Union[Callable, Type], **kwargs) -> Type:
    if inspect.isfunction(func_or_cls):
        # check for cython via ray._private.inspect_util.is_cython?
        return func_as_comp(execute=func_or_cls, **kwargs)
    if inspect.isclass(func_or_cls):
        return class_as_comp(cls=func_or_cls, **kwargs)
    raise TypeError("The @component decorator must be applied to either a function or a class.")


def _get_hint(execute: Callable, model_type: str, Model: Type[DataModel] = None):
    # Try to infer model types if unspecified
    if Model is None:
        Model = get_type_hints(execute).get(model_type)
        if Model is None:
            raise AttributeError(
                f"Execution function {execute.__name__} must annotate {model_type}."
            )
        if isinstance(Model, str):
            try:
                module_name, model_name = Model.rsplit(".", maxsplit=1)
                module = importlib.import_module(module_name)
                Model = getattr(module, model_name, None)
            except Exception:
                raise AttributeError(f"Could not infer model type for {Model} from given hint.")

    try:
        assert issubclass(Model, DataModel), f"Class {Model} is not a subclass of DataModel"
    except TypeError:
        raise TypeError(f"Data model ({Model}) is not a class.")

    return Model


def _split_kwargs(
    execute: Callable,
    **kwargs,
) -> Tuple[Type[ComponentRoot], Type[DataModel], Type[DataModel], Dict[str, Any]]:
    ComponentType = getattr(ComponentTypes, kwargs.get("ctype", "default"), None)
    InModel = kwargs.get("in_model", None)
    OutModel = kwargs.get("out_model", None)
    compute_req = {
        key: kwargs[key] for key in kwargs if key not in ["ctype", "in_model", "out_model", "meta"]
    }

    if ComponentType is None:
        raise NotImplementedError(f"Component type {ComponentType} not supported.")

    InModel = _get_hint(execute, "input_model", InModel)
    OutModel = _get_hint(execute, "return", OutModel)

    return ComponentType.value, InModel, OutModel, compute_req


def check_reserved_keyword(cls):
    # reserved properties/methods in components
    for attribute in [
        "compute",
        "input",
        "output",
        "compute_remote",  # need to generalize
    ]:
        if hasattr(cls, attribute):
            raise AttributeError(f"Class {cls.__name__} already defines attribute `{attribute}`.")


def meta_as_comp(cls: Type, **kwargs) -> Type:
    check_reserved_keyword(cls)

    InModel = kwargs.get("in_model", None)
    assert InModel
    assert issubclass(InModel, DataModel)

    OutModel = kwargs.get("out_model", None)
    assert OutModel
    assert issubclass(OutModel, DataModel)

    namespace = {
        "__module__": cls.__module__,
        "__qualname__": cls.__qualname__,
        "__doc__": cls.__doc__,
        "_from_meta": functools.partial(class_as_comp, **kwargs),
        "input": InModel,
        "output": OutModel,
        "__annotations__": {"input": ClassVar(InModel), "output": ClassVar(OutModel)},
    }
    MetaMetaComp, _, _ = types.prepare_class(
        f"MetaComponent({cls.__name__})",
        (cls, MetaComponentRay),  # need to generalize
    )

    MetaComp = MetaMetaComp(f"MetaComponent({cls.__name__})", (cls, MetaComponentRay), namespace)

    return MetaComp


def class_as_comp(cls: Type, **kwargs) -> Type[ComponentRoot]:
    # Should we allow overriding existing components?
    # check_reserved_keyword(cls)

    # if issubclass(cls, ComponentRoot):
    #    raise TypeError("Cannot subclass an existing ComponentRoot subclass.")

    assert getattr(cls, "execute", None), f"Component {cls} must define `execute` instance method."
    assert callable(
        cls.execute
    ), f"Component {cls} or its base class must define `execute` instance method"

    ComponentType, InModel, OutModel, compute_req = _split_kwargs(cls.execute, **kwargs)

    # Make sure the new component we are constructing inherits from the
    # original class so it retains all class properties.

    namespace: dict[str, Any] = {
        "__module__": cls.__module__,
        "__qualname__": cls.__qualname__,
        "__doc__": cls.__doc__,
        "__annotations__": {},
    }

    # Do not create fields if fwd declared
    if not isinstance(InModel, str):
        namespace["__annotations__"]["input"] = ClassVar[InModel]
        namespace["input"] = InModel

    if not isinstance(OutModel, str):
        namespace["__annotations__"]["output"] = ClassVar[OutModel]
        namespace["output"] = OutModel

    NewMetaClass, _, _ = types.prepare_class(
        f"Component({cls.__name__})",
        (cls, ComponentType),
    )

    NewClass = NewMetaClass(f"Component({cls.__name__})", (cls, ComponentType), namespace)

    if compute_req:
        assert issubclass(
            ComponentType, ComponentRay
        ), f"ComponentType {ComponentType} does not support remote compute"
        exec_req = ExecReq(compute_req=compute_req)
        NewClass._compute_remote = compute_remote(NewClass, exec_req)

    return NewClass


def func_as_comp(execute: Callable, **kwargs) -> Type:
    ComponentType, InModel, OutModel, compute_req = _split_kwargs(execute, **kwargs)

    execute.__annotations__["input_model"] = InModel
    execute.__annotations__["return"] = OutModel

    @functools.wraps(execute)
    def wrapper(*args, **kwargs) -> Type:
        namespace: dict[str, Any] = {
            "execute": lambda self, input_model, exec_req, **kwargs: execute(
                input_model, exec_req, **kwargs
            ),
            "__module__": ComponentType.__module__,
            "__annotations__": {},
        }

        # Do not create fields if fwd declared
        if not isinstance(InModel, str):
            namespace["__annotations__"]["input"] = ClassVar[InModel]
            namespace["input"] = InModel

        if not isinstance(OutModel, str):
            namespace["__annotations__"]["output"] = ClassVar[OutModel]
            namespace["output"] = OutModel

        MetaComponent, _, _ = types.prepare_class(
            f"Component({execute.__name__})",
            (ComponentType,),
        )

        Component = MetaComponent(f"Component({execute.__name__})", (ComponentType,), namespace)

        if compute_req:
            assert issubclass(ComponentType, ComponentRay)
            exec_req = ExecReq(compute_req=compute_req)
            Component._compute_remote = compute_remote(Component, exec_req)
        return Component

    return wrapper(**kwargs)


def component(*args, **kwargs) -> Type:
    """
    Decorator designed to transform a function into ComponentRoot.compute.
    The function signature must be the same as the execute function.

    Parameters
    ----------
    in_model: DataModel, optional
        An immutable input data class that defines the required and optional fields for execution.
    out_model: DataModel, optional
        An immutable output data class that defines the required and optional fields.

    Returns
    -------
    Type
        A new component class that has the following 2 attributes: `input_model` and `output_model`
        and at least one single public (`compute`) classmethod.

    Raises
    ------
    AttributeError
        If the input_model or output_model attribute in the decorated function already exists,
        or if the execution function is not properly annotated.

    Examples
    --------
    >>> @component
        def foo(input_model: InputModel, **kwargs) -> OutputModel:
            # Do something with input_model
            ...
            return output_data

    >>> @component(in_model=InputModel, out_model=OutputModel, **compute_req)
        def foo(input_model, **kwargs) -> OutputModel:
            # Do something with input_model
            ...
            return output_data

    >>> # Usage: foo.compute(input_data={...}, exec_req={...})

    """

    # Case: @component
    if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
        return _comp_adapter(args[0])

    assert (
        len(args) == 0 and len(kwargs) > 0
    ), "Decorator usage: @component or @component(**kwargs)"

    # Case: @component(meta=...)
    if kwargs.get("meta"):
        return functools.partial(meta_as_comp, **kwargs)

    # Case: @component(**kwargs)
    return functools.partial(_comp_adapter, **kwargs)
