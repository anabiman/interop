from typing import Any, Optional

from ..models import DataModel
from ..utils.data import Field
from ..utils.dtypes import DirectoryPath, PositiveFloat, PositiveInt


class ComputeReq(DataModel):
    num_gpus: Optional[int] = Field(None, description="Number of GPU devices to reserve.")
    num_cpus: Optional[int] = Field(None, description="Number of CPU cores to reserve.")
    num_returns: Optional[int] = Field(
        None,
        description="Number of object refs returned by the remote function invocation.",
    )
    memory: Optional[PositiveFloat] = Field(
        None, description="Amount of heap memory to allocate (in bytes)."
    )
    object_store_memory: Optional[PositiveFloat] = Field(
        None, description="Amount of memory (in bytes) to start the object store with."
    )
    resources: Optional[dict[str, PositiveFloat]] = Field(
        None, description="Quantity of various custom resources to reserve."
    )
    max_calls: Optional[PositiveInt] = Field(
        None,
        description="Max number of times that an execute function can be run before"
        " it must exit.",
    )
    max_retries: Optional[int] = Field(
        4,
        description="Maximum number of times that the execute function should be rerun when the "
        "worker process executing it crashes unexpectedly. The minimum valid value is 0, the "
        "default is 4 (default), and a value of -1 indicates infinite retries.",
    )
    runtime_env: Optional[dict[str, Any]] = Field(
        None,
        description="Specifies the runtime environment to execute a specific component in.",
    )
    retry_exceptions: Optional[bool] = Field(
        None,
        description="specifies whether application-level errors should be retried up to"
        " *max_retries times*.",
    )


class ExecReq(DataModel):
    """
    This data class is useful for workflow management systems or parallel/compute
    frameworks. For instance, the *resource_alloc* field is an exact fit for the compute
    framework ``Ray`` (https://ray.io) that allows a component to be executed remotely.
    """

    compute_req: Optional[ComputeReq] = Field(None, description="Runtime compute requirements.")
    address: Optional[str] = Field(None, description="Address of cluster to connect to.")
    thread_safe: Optional[bool] = Field(
        False, description="Specifies implementation thread safety."
    )
    scratch_dir: Optional[DirectoryPath] = Field(None, description="Path to scratch dir.")
