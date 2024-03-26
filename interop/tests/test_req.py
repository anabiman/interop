import os

from interop.models.req import ExecReq


def test_req():
    conf = ExecReq(
        thread_safe=False,
        scratch_dir=os.getcwd(),
        address="8.8.8.8:80",
        compute_req={"num_cpus": 1, "num_gpus": 1, "memory": 8},
    )
    conf.model_dump()
    conf.json()
    ExecReq.model_validate(conf)
