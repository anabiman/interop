from typing import Any, Dict, Type

import pytest
from pydantic import ValidationError

from interop.common.components import ComponentTypes, get_models
from interop.models import DataModel
from interop.utils.decorators import component


class DataFoo(DataModel):
    pass


class DummyModel(DataModel):
    field: int


@pytest.mark.parametrize(
    "component_type",
    [ctype.value for ctype in ComponentTypes],
)
def test_components(component_type: Type):
    gen_component = type("component", (component_type,), {"execute": lambda self: 0})
    assert gen_component
    assert getattr(gen_component, "compute", None)
    assert callable(gen_component.compute)


def test_component_hints_fail():
    def execute(input_model, exec_req, **kwargs):
        return DataFoo()

    with pytest.raises(AttributeError):
        component(execute)

    def execute(input_model, exec_req: Dict[str, Any] = None):
        return DataFoo()

    with pytest.raises(AttributeError):
        component(execute)


def test_component_valid_fail():
    def execute(input_model, exec_req=None, **kwargs):
        return DataFoo()

    comp = component(in_model=DataFoo, out_model=DataFoo)(execute)

    with pytest.raises(ValidationError):
        input = DummyModel(field=1)
        comp.compute(input_data=input)


# Test decorators
def test_func_hints():
    def foo(input_model: DummyModel, exec_req=None, **kwargs) -> DummyModel:
        return DummyModel(field=0)

    in_model, out_model = get_models(foo)
    assert issubclass(in_model, DummyModel)
    assert issubclass(out_model, DummyModel)

    comp_foo = component(foo)

    out = comp_foo.compute(DummyModel(field=1))
    DummyModel.model_validate(out.model_dump())
    assert out.field == 0


def test_func_nohints():
    def foo(input_model, exec_req=None, **kwargs):
        return DummyModel(field=0)

    in_model, out_model = get_models(foo)
    assert in_model is None
    assert out_model is None

    comp_foo = component(in_model=DummyModel, out_model=DummyModel)(foo)

    out = comp_foo.compute(DummyModel(field=1))
    DummyModel.model_validate(out.model_dump())
    assert out.field == 0


def test_class_hints():
    @component
    class Component:
        def execute(self, input_model: DummyModel, exec_req=None, **kwargs) -> DummyModel:
            return DummyModel(field=0)

    out = Component.compute(DummyModel(field=1))
    DummyModel.model_validate(out.model_dump())
    assert out.field == 0

    assert issubclass(Component.input, DummyModel)
    assert issubclass(Component.output, DummyModel)


def test_class_nohints():
    @component(in_model=DummyModel, out_model=DummyModel)
    class Component:
        def execute(self, input_model, exec_req=None, **kwargs):
            return DummyModel(field=0)

    out = Component.compute(DummyModel(field=1, schema_name="my_schema", schema_version=1))
    DummyModel.model_validate(out.model_dump())
    assert out.field == 0

    assert issubclass(Component.input, DummyModel)
    assert issubclass(Component.output, DummyModel)


def test_class_raise():
    with pytest.raises(TypeError):

        @component(in_model=DummyModel, out_model=DummyModel)
        class Component:
            def execute(self, input_model, exec_req=None, **kwargs):
                return DummyModel(field=0)

            def compute():
                pass

        Component.compute(DummyModel(field=1))
