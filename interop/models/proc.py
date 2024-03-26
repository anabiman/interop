from typing import TYPE_CHECKING, Any, Dict, Optional

from pydantic import Field, NonNegativeFloat

from ..utils.data import provenance_stamp
from .data import DataModel

if TYPE_CHECKING:
    from pydantic.typing import ReprArgs

__all__ = ["InputProc", "OutputProc"]


class Provenance(DataModel):
    """Provenance information."""

    creator: str = Field(
        ...,
        description="The name of the program, library, or person who created the object.",
    )
    version: str = Field(
        "",
        description="The version of the creator, blank otherwise. This should be sortable"
        " by the very broad [PEP 440](https://www.python.org/dev/peps/pep-0440/).",
    )
    routine: str = Field(
        "",
        description="The name of the routine or function within the creator, blank otherwise.",
    )


class ComputeError(DataModel):
    """Complete description of the error from an unsuccessful program execution."""

    error_type: str = Field(  # type: ignore
        ...,  # Error enumeration not yet strict
        description="The type of error which was thrown. Restrict this field to short"
        " classifiers e.g. 'input_error'.",
    )
    error_message: str = Field(  # type: ignore
        ...,
        description="Text associated with the thrown error. This is often the backtrace,"
        " but it can contain additional information as well.",
    )
    extras: Optional[Dict[str, Any]] = Field(  # type: ignore
        None,
        description="Additional information to bundle with the error.",
    )

    class ConfigDict:
        repr_style = ["error_type", "error_message"]

    def __repr_args__(self) -> "ReprArgs":
        return [("error_type", self.error_type), ("error_message", self.error_message)]


class FailedOperation(DataModel):
    """
    Record indicating that a given operation (program, procedure, etc.) has failed and
    containing the reason and input data which generated the failure."""

    input_data: Any = Field(  # type: ignore
        None,
        description="The input data which was passed in that generated this failure. "
        "This should be the complete input which when attempted to be run, caused "
        "the operation to fail.",
    )
    success: bool = Field(  # type: ignore
        False,
        description="A boolean indicator that the operation failed consistent "
        "with the model of successful operations. Should always be False. Allows "
        "programmatic assessment of all operations regardless of if they failed or succeeded",
    )
    error: ComputeError = Field(  # type: ignore
        ...,
        description="A container which has details of the error that failed this operation. "
        "See the :class:`ComputeError` for more details.",
    )
    extras: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional information to bundle with the failed operation. "
        "Details which pertain specifically to a thrown error should be contained "
        "in the `error` field. See :class:`ComputeError` for details.",
    )

    def __repr_args__(self) -> "ReprArgs":
        return [("error", self.error)]


class InputProc(DataModel):
    id: Optional[str] = None
    keywords: Optional[Dict[str, Any]] = Field(
        {}, description="Procedure specific keywords to be used."
    )
    provenance: Optional[Provenance] = Field(
        Provenance(**provenance_stamp(__name__)), description=str(Provenance.__doc__)
    )
    delay: Optional[NonNegativeFloat] = Field(
        5, description="How long to wait (in seconds) for filesystem read buffer."
    )
    logger: Optional[Any] = Field(
        None, description="Logging object or path to log file/name/etc.."
    )
    engine: Optional[str] = Field(
        None,
        description="Engine name to use in the procedure e.g. OpenMM.",
    )
    engine_version: Optional[str] = Field(
        None, description="Supported engine version. e.g. '>=3.4.0'."
    )
    extras: Optional[Dict[str, Any]] = Field(
        {}, description="Extra fields that are not part of the schema."
    )


class OutputProc(DataModel):
    proc_input: Optional[InputProc] = None
    stdout: Optional[str] = Field(None, description="The standard output of the program.")
    stderr: Optional[str] = Field(None, description="The standard error of the program.")
    warnings: Optional[str] = Field(None, description="Warning messages.")
    delay: Optional[NonNegativeFloat] = Field(
        5, description="How long to wait (in seconds) for filesystem write buffer"
    )
    log: Optional[str] = Field(None, description="Logging info.")
    success: bool = Field(
        ...,
        description="The success of a given programs execution. If False, other fields"
        " may be blank.",
    )
    error: Optional[ComputeError] = Field(None, description=str(ComputeError.__doc__))
    provenance: Optional[Provenance] = Field(
        Provenance(**provenance_stamp(__name__)), description=str(Provenance.__doc__)
    )
    extras: Optional[Dict[str, Any]] = Field(
        {}, description="Extra fields that are not part of the schema."
    )
