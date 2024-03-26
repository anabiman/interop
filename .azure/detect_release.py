import re
import subprocess
from pathlib import Path

from mds_dev.utils import env_run_stdout

DEFAULT_BRANCH = "main"


def _validate_tag(tag):
    """
    Tags must match semver structure (e.g. 1.0.0) whenever tagging the default branch. Otherwise
    deployment automations will not happen.

    Any non-default branch must match the semver alpha structure (e.g. 2.1.1a9), otherwise
    deployment automations will not happen.
    """
    # branch = env_run_stdout(
    #    f"git checkout HEAD && git branch -a --contains tags/{tag} | grep '*'"
    # )
    # branch = branch.split("*")[-1].strip()
    branch = "main"

    if branch == DEFAULT_BRANCH and not re.match(r"^\d+\.\d+\.\d+$", tag):
        return False
        # f'Tag "{tag}" for "{DEFAULT_BRANCH}" branch is invalid. Must be in form of "<MAJOR>.<MINOR>.<PATCH>'
    elif branch != DEFAULT_BRANCH and not re.match(r"^\d+\.\d+\.\d+a\d+$", tag):
        return False
        # f'Tag "{tag}" for "{branch}" branch is invalid. Must be in form of "<MAJOR>.<MINOR>.<PATCH>a<BUILD>'
    else:
        return True


def is_stable_release(directory: Path) -> bool:
    output = subprocess.run(
        ["git", "tag", "--points-at", "HEAD"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        cwd=directory,
    )
    tag = output.stdout.decode("utf-8").strip()
    if re.match(r"^[a-z0-9.]+$", tag):  # accept only alphanum with dot
        return _validate_tag(tag)
    else:
        return False


if __name__ == "__main__":
    print(is_stable_release("."))
