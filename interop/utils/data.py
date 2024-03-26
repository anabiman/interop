from pydantic import Field, root_validator, validator

__all__ = ["Field", "root_validator", "validator"]


def provenance_stamp(routine, version="", creator=__name__):
    return {
        "creator": creator,
        "version": version,
        "routine": routine,
    }
