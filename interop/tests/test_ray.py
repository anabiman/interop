import ipaddress
import logging
import random
from sys import platform

import psutil
import pytest
import ray

import interop.utils.ray
from interop import component
from interop.models import DataModel
from interop.models.req import ExecReq


def test_remote_execute():
    def foo(input_model: DataModel, exec_req: ExecReq, **kwargs) -> DataModel:
        return DataModel(schema_name="foo", schema_version=1)

    num_workers = psutil.cpu_count()

    compute_req = {"num_cpus": 1}

    # Override compute_req
    Comp = component(ctype="ray", **compute_req)(foo)
    tasks = [
        Comp.compute_remote(input_data={}, exec_req={"compute_req": compute_req})
        for _ in range(num_workers)
    ]

    for result in ray.get(tasks):
        assert result.schema_name == "foo"
        assert result.schema_version == 1

    # Preserve compute_req
    Comp = component(ctype="ray", **compute_req)(foo)
    tasks = [Comp.compute_remote(input_data={}) for _ in range(num_workers)]

    for result in ray.get(tasks):
        assert result.schema_name == "foo"
        assert result.schema_version == 1

    ray.shutdown()


@pytest.mark.parametrize(
    "ip,version",
    [
        (str(ipaddress.IPv4Address(random.randint(0, 2**32))), "IPv4"),
        (str(ipaddress.IPv6Address(random.randint(0, 2**128))), "IPv6"),
        ("1.0", "Invalid"),
    ],
)
def test_valid(ip, version):
    assert interop.utils.ray.validIPAddress(ip) == version


def test_slurm_fail():
    with pytest.raises(KeyError):
        interop.utils.ray.create_cluster()


@pytest.mark.skipif("linux" not in platform, reason="Port detection supported only on Linux")
def test_port():
    assert interop.utils.ray.get_port().isdigit()


@pytest.mark.parametrize(
    "logger,exec_req", [(None, None), (logging.Logger, {"compute_req": {"num_cpus": 1}})]
)
def test_initialize_ray(logger: logging.Logger, exec_req: dict[str, str]):
    num_cpus, num_gpus = interop.utils.ray.initialize_ray()
    assert num_cpus > 0
    if num_gpus is not None:
        assert num_gpus > 0
    ray.shutdown()
    assert not ray.is_initialized()
