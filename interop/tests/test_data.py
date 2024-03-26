from interop.models import DataModel


def test_data_basic():
    data = DataModel()
    str(data)
    data.model_dump()
    data.json()
    repr(data)
    data.default_schema_name


def test_data_serialize():
    data = DataModel()
    data.serialize(encoding="json")
    data.serialize(encoding="json", indent=4)
