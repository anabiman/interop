""" Adopted from https://github.com/andrew-abimansour/QCEngine/blob/execute/qcengine/util.py
This is a modified version of MolSSI's QCEngine executor util module. """

import io
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from functools import partial
from pathlib import Path
from threading import Thread
from typing import Any, BinaryIO, Dict, List, Optional, TextIO, Tuple, Union


def terminate_process(proc: Any, timeout: int = 15) -> None:  # pragma: no cover
    if proc.poll() is None:
        # Sigint (keyboard interupt)
        if sys.platform.startswith("win"):
            proc.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            proc.send_signal(signal.SIGINT)

        try:
            start = time.time()
            while (proc.poll() is None) and (time.time() < (start + timeout)):
                time.sleep(0.02)

        # Flat kill
        finally:
            proc.kill()


@contextmanager  # pragma: no cover
def popen(
    args: List[str],
    append_prefix: bool = False,
    popen_kwargs: Optional[Dict[str, Any]] = None,
    pass_output_forward: bool = False,
) -> Dict[str, Any]:
    """
    Opens a background task
    Code and idea from dask.distributed's testing suite
    https://github.com/dask/distributed
    Parameters
    ----------
        args: List[str]
            Input arguments for the command
        append_prefix: bool
            Whether to prepend the Python path prefix to the command being executed
        popen_kwargs: Dict[str, Any]
            Any keyword arguments to use when launching the process
        pass_output_forward: bool
            Whether to pass the stdout and stderr forward to the system's stdout and stderr
    Returns
    -------
        exe: dict
            Dictionary with the following keys:
            <ul>
                <li>proc: Popen object describing the background task</li>
                <li>stdout: String value of the standard output of the task</li>
                <li>stdeer: String value of the standard error of the task</li>
            </ul>
    """
    args = list(args)
    if popen_kwargs is None:
        popen_kwargs = {}
    else:
        popen_kwargs = popen_kwargs.copy()

    # Bin prefix
    if sys.platform.startswith("win"):
        bin_prefix = os.path.join(sys.prefix, "Scripts")
    else:
        bin_prefix = os.path.join(sys.prefix, "bin")

    # Do we prefix with Python?
    if append_prefix:
        args[0] = os.path.join(bin_prefix, args[0])

    if sys.platform.startswith("win"):
        # Allow using CTRL_C_EVENT / CTRL_BREAK_EVENT
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

    # Route the standard error and output
    popen_kwargs["stdout"] = subprocess.PIPE
    popen_kwargs["stderr"] = subprocess.PIPE

    # Prepare StringIO objects to store the stdout and stderr
    stdout = io.BytesIO()
    stderr = io.BytesIO()

    # Ready the output
    ret = {"proc": subprocess.Popen(args, **popen_kwargs)}

    # Spawn threads that will read from the stderr/stdout
    #  The PIPE uses a buffer with finite capacity. The underlying
    #  process will stall if it is unable to write to the buffer
    #  because the buffer is full. These threads continuously read
    #  from the buffers to ensure that they do not fill.
    #
    def read_from_buffer(buffer: BinaryIO, storage: io.BytesIO, sysio: TextIO):
        for r in iter(partial(buffer.read, 1024), b""):
            storage.write(r)
            if pass_output_forward:
                sysio.write(r.decode())

    stdout_reader = Thread(target=read_from_buffer, args=(ret["proc"].stdout, stdout, sys.stdout))
    stdout_reader.start()
    stderr_reader = Thread(target=read_from_buffer, args=(ret["proc"].stderr, stderr, sys.stderr))
    stderr_reader.start()

    # Yield control back to the main thread
    try:
        yield ret
    except Exception:
        raise

    finally:
        # Executes on an exception or once the context manager closes
        try:
            terminate_process(ret["proc"])
        finally:
            # Wait for the reader threads to finish
            stdout_reader.join()
            stderr_reader.join()

            # Retrieve the standard output for the process
            ret["stdout"] = stdout.getvalue().decode()
            ret["stderr"] = stderr.getvalue().decode()


@contextmanager  # pragma: no cover
def environ_context(config: Any = None, env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Temporarily set environment variables inside the context manager and
    fully restore previous environment afterwards.
    Parameters
    ----------
    config : Any, optional
        Automatically sets MKL/OMP num threads based off the input config.
    env : Optional[Dict[str, str]], optional
        A dictionary of environment variables to update.

    Yields
    ------
    Dict[str, str]
        The updated environment variables.

    """

    temporary_env = {}
    if config:
        temporary_env["OMP_NUM_THREADS"] = str(config.ncores)
        temporary_env["MKL_NUM_THREADS"] = str(config.ncores)

    if env:
        temporary_env.update(env)

    original_env = {key: os.getenv(key) for key in temporary_env}
    os.environ.update(temporary_env)
    try:
        yield temporary_env
    finally:
        for key, value in original_env.items():
            if value is None:
                del os.environ[key]
            else:
                os.environ[key] = value


def execute(
    command: List[str],
    infiles: Optional[Dict[str, str]] = None,
    outfiles: Optional[List[str]] = None,
    *,
    outfiles_track: Optional[List[str]] = None,
    as_binary: Optional[List[str]] = None,
    scratch_name: Optional[str] = None,
    scratch_directory: Optional[str] = None,
    scratch_suffix: Optional[str] = None,
    scratch_messy: bool = False,
    scratch_exist_ok: bool = False,
    blocking_files: Optional[List[str]] = None,
    timeout: Optional[int] = None,
    interupt_after: Optional[int] = None,
    environment: Optional[Dict[str, str]] = None,
    shell: Optional[bool] = False,
    exit_code: Optional[int] = 0,
) -> Tuple[bool, Dict[str, Any]]:  # pragma: no cover
    """
    Runs a process in the background until complete.
    Returns True if exit code <= exit_code (default 0)

    Parameters
    ----------
    command : list of str
    infiles : Dict[str] = str
        Input file names (names, not full paths) and contents.
        to be written in scratch dir. May be {}.
    outfiles : List[str] = None
        Output file names to be collected after execution into
        values. May be {}.
    outfiles_track: List[str], optional
        Keys of `outfiles` to keep track of without loading their contents in memory.
        For specified filename in `outfiles_track`, the file path instead of contents
        is stored in `outfiles`. To ensure tracked files are not deleted after execution,
        you must set `scratch_messy=True`.
    as_binary : List[str] = None
        Keys of `infiles` or `outfiles` to be treated as bytes.
    scratch_name : str, optional
        Passed to temporary_directory
    scratch_directory : str, optional
        Passed to temporary_directory
    scratch_suffix : str, optional
        Passed to temporary_directory
    scratch_messy : bool, optional
        Passed to temporary_directory
    scratch_exist_ok : bool, optional
        Passed to temporary_directory
    blocking_files : list, optional
        Files which should stop execution if present beforehand.
    timeout : int, optional
        Stop the process after n seconds.
    interupt_after : int, optional
        Interupt the process (not hard kill) after n seconds.
    environment : dict, optional
        The environment to run in
    shell : bool, optional
        Run command through the shell.
    exit_code: int, optional
        The exit code above which the process is considered failure.

    Raises
    ------
    FileExistsError
        If any file in `blocking` is present

    Examples
    --------
    # execute multiple commands in same dir
    >>> success, dexe = qcng.util.execute(['command_1'], infiles, [], scratch_messy=True)
    >>> success, dexe = qcng.util.execute(['command_2'], {}, outfiles, scratch_messy=False,
        scratch_name=Path(dexe['scratch_directory']).name, scratch_exist_ok=True)

    """

    # Format inputs
    if infiles is None:
        infiles = {}

    if outfiles is None:
        outfiles = []
    outfiles = {k: None for k in outfiles}

    # Check for blocking files
    if blocking_files is not None:
        for fl in blocking_files:
            if os.path.isfile(fl):
                raise FileExistsError("Existing file can interfere with execute operation.", fl)

    # Format popen
    popen_kwargs = {}
    if environment is not None:
        popen_kwargs["env"] = {k: v for k, v in environment.items() if v is not None}

    # Execute
    with temporary_directory(
        child=scratch_name,
        parent=scratch_directory,
        messy=scratch_messy,
        exist_ok=scratch_exist_ok,
        suffix=scratch_suffix,
    ) as scrdir:
        popen_kwargs["cwd"] = scrdir
        popen_kwargs["shell"] = shell
        with disk_files(
            infiles,
            outfiles,
            cwd=scrdir,
            as_binary=as_binary,
            outfiles_track=outfiles_track,
        ) as extrafiles:
            with popen(command, popen_kwargs=popen_kwargs) as proc:
                # Wait for the subprocess to complete or the timeout to expire
                if interupt_after is None:
                    proc["proc"].wait(timeout=timeout)
                else:
                    time.sleep(interupt_after)
                    terminate_process(proc["proc"])
            retcode = proc["proc"].poll()
        proc["outfiles"] = extrafiles
    proc["scratch_directory"] = scrdir

    return retcode <= exit_code, proc


@contextmanager  # pragma: no cover
def temporary_directory(
    child: str = None,
    *,
    parent: str = None,
    suffix: str = None,
    messy: bool = False,
    exist_ok: bool = False,
) -> str:
    """Create and cleanup a quarantined working directory with a parent scratch directory.
    Parameters
    ----------
    child : str, optional
        By default, `None`, quarantine directory generated through
        `tempfile.mdktemp` so guaranteed unique and safe. When specified,
        quarantine directory has exactly `name`.
    parent : str, optional
        Create directory `child` elsewhere than TMP default.
        For TMP default, see https://docs.python.org/3/library/tempfile.html#tempfile.gettempdir
    suffix : str, optional
        Create `child` with identifying label by passing to ``tempfile.mkdtemp``.
        Encouraged use for debugging only.
    messy : bool, optional
        Leave scratch directory and contents on disk after completion.
    exist_ok : bool, optional
        Run commands in a possibly pre-existing directory.
    Yields
    ------
    str
        Full path of scratch directory.
    Raises
    ------
    FileExistsError
        If `child` specified and directory already exists (perhaps from a
        previous `messy=True` run).
    Examples
    --------
    parent            child     suffix   -->  creates
    ------            -----     ------        -------
    None              None      None     -->  /tmp/tmpliyp1i7x/
    None              None      _anharm  -->  /tmp/tmpliyp1i7x_anharm/
    None              myqcjob   None     -->  /tmp/myqcjob/
    /scratch/johndoe  None      None     -->  /scratch/johndoe/tmpliyp1i7x/
    /scratch/johndoe  myqcjob   None     -->  /scratch/johndoe/myqcjob/
    """
    if child is None:
        tmpdir = Path(tempfile.mkdtemp(dir=parent, suffix=suffix))
    else:
        if parent is None:
            parent = Path(tempfile.gettempdir())
        else:
            parent = Path(parent)
        tmpdir = parent / child
        try:
            os.mkdir(tmpdir)
        except FileExistsError:
            if exist_ok:
                pass
            else:
                raise
    try:
        yield tmpdir

    finally:
        if not messy:
            shutil.rmtree(tmpdir)


@contextmanager
def disk_files(
    infiles: Dict[str, Union[str, bytes]],
    outfiles: Dict[str, None],
    *,
    cwd: Optional[str] = None,
    as_binary: Optional[List[str]] = None,
    outfiles_track: Optional[List[str]] = None,
) -> Dict[str, Union[str, bytes, Path]]:  # pragma: no cover
    """Write and collect files.
    Parameters
    ----------
    infiles : Dict[str] = str
        Input file names (names, not full paths) and contents.
        to be written in scratch dir. May be {}.
    outfiles : Dict[str] = None
        Output file names to be collected after execution into
        values. May be {}.
    cwd : str, optional
        Directory to which to write and read files.
    as_binary : List[str] = None
        Keys in `infiles` (`outfiles`) to be written (read) as bytes, not decoded.
    outfiles_track: List[str], optional
        Keys of `outfiles` to keep track of (i.e. file contents not loaded in memory).
        For specified filename in `outfiles_track`, the file path instead of contents
        is stored in `outfiles`.
    Yields
    ------
    Dict[str, Union[str, bytes, Path]]
        outfiles with RHS filled in.
    """
    if cwd is None:
        lwd = Path.cwd()
    else:
        lwd = Path(cwd)
    if as_binary is None:
        as_binary = []
    assert set(as_binary) <= (set(infiles) | set(outfiles))

    outfiles_track = outfiles_track or []

    try:
        for fl, content in infiles.items():
            omode = "wb" if fl in as_binary else "w"
            filename = lwd / fl
            with open(filename, omode) as fp:
                fp.write(content)

        yield outfiles

    finally:
        outfiles_track = [
            fpath.name if "*" in track else track
            for track in outfiles_track
            for fpath in lwd.glob(track)
        ]
        for fl in outfiles.keys():
            filename = lwd / fl
            omode = "rb" if fl in as_binary else "r"
            try:
                with open(filename, omode) as fp:
                    if fl not in outfiles_track:
                        outfiles[fl] = fp.read()
                    else:
                        outfiles[fl] = filename
            except OSError:
                if "*" in fl:
                    gfls = {}
                    for gfl in lwd.glob(fl):
                        with open(gfl, omode) as fp:
                            if gfl.name not in outfiles_track:
                                gfls[gfl.name] = fp.read()
                            else:
                                gfls[gfl.name] = gfl
                    if not gfls:
                        gfls = None
                    outfiles[fl] = gfls
                else:
                    outfiles[fl] = None
