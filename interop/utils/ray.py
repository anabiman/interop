import logging
import os
import resource
import subprocess
import tempfile
from ipaddress import IPv4Address, ip_address
from time import sleep
from typing import Any, List, Optional

import ray

from interop.models.req import ExecReq


def validIPAddress(ip: str) -> str:
    """
    Validates an IPv4 address.

    Parameters
    ----------
    ip: str
        I.P. address to validate

    Returns
    -------
    str
        `IPv4` or `IPv6` if address is a valid otherwise `Invalid`.
    """
    try:
        return "IPv4" if isinstance(ip_address(ip), IPv4Address) else "IPv6"
    except ValueError:
        return "Invalid"


def pipe_process(cmd: list[str], stdin: Optional[bytes] = None) -> bytes:
    """
    Creates and runs a process with stdin, stdout, and stderr piped.

    Parameters
    ----------
    cmd: list[str]
        Command with args to run
    stdin: Optional[bytes]
        Input to pipe to the process

    Returns
    -------
    bytes
        Standard output

    Raises
    ------
    RuntimeError
        If process fails with stderr not None

    """
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE
    )
    stdout, stderr = proc.communicate(input=stdin)
    if stderr:
        raise RuntimeError(stderr)
    return stdout


def set_rlimit() -> None:
    """Sets max number of open files to the hard limit."""
    _, hard_lim = resource.getrlimit(resource.RLIMIT_NOFILE)
    resource.setrlimit(resource.RLIMIT_NOFILE, (hard_lim, hard_lim))


def get_port() -> str:
    """
    Returns an unreserved port number. This executes the following bash
    script:

    .. code-block:: bash

       $ port=`comm -23 <(seq 49152 65535) <(ss -tan | awk '{print $4}' | cut -d':' \\
       $ -f2 | grep "[0-9]\\{1,5\\}" | sort | uniq) | shuf | head -n 1`

    `Source <https://roivant.atlassian.net/wiki/spaces/~865930246/pages/2610397223/ray+on+neo>`_

    Returns
    -------
    str
        Port number
    """
    stdout1 = pipe_process(["seq", "49152", "65535"])
    stdout2 = pipe_process(["ss", "-tan"])
    stdout3 = pipe_process(["awk", '"{print $4}"'], stdin=stdout2)
    stdout4 = pipe_process(["cut", "-d", ":", "-f2"], stdin=stdout3)
    stdout5 = pipe_process(["grep", "[0-9]\\{1,5\\}"], stdin=stdout4)
    stdout6 = pipe_process(["sort"], stdin=stdout5)
    stdout7 = pipe_process(["uniq"], stdin=stdout6)

    with tempfile.NamedTemporaryFile(delete=True) as tmp1:
        tmp1.write(stdout1)
        with tempfile.NamedTemporaryFile(delete=True) as tmp2:
            tmp2.write(stdout7)
            stdout8 = pipe_process(["comm", "-23", tmp1.name, tmp2.name])

    stdout9 = pipe_process(["shuf"], stdin=stdout8)
    return pipe_process(["head", "-n", "1"], stdin=stdout9).decode("utf-8").strip()


def setup_head_node() -> tuple[str, str, str, list[str]]:
    """Sets up Ray head node, and returns info required to create a Ray cluster.

    Returns
    -------
    tuple[str, str, str, list[str]]
        Head node id, head node ip address, port number, and list of all worker nodes

    Raises
    ------
    RuntimeError
        If head node creation fails

    AssertionError
        If head node ip address is not a valid IPv4

    """

    try:
        slurm_job_nodelist = os.environ["SLURM_JOB_NODELIST"]
    except KeyError:
        raise KeyError(
            "Env variable SLURM_JOB_NODELIST is undefined. Are you running from within SLURM?"
        )

    out = subprocess.run(
        ["scontrol", "show", "hostnames", slurm_job_nodelist], capture_output=True
    )
    nodes_array = out.stdout.decode("utf-8").strip("\n").split("\n")

    head_node = nodes_array[0]

    proc = subprocess.run(
        ["srun", "--nodes=1", "--ntasks=1", "-w", head_node, "hostname", "--ip-address"],
        capture_output=True,
    )

    stderr = proc.stderr.decode("utf-8")
    if stderr:
        raise RuntimeError(stderr)

    head_node_ip = proc.stdout.decode("utf-8").strip()
    assert validIPAddress(head_node_ip) == "IPv4"

    port = get_port()

    return head_node, head_node_ip, port, nodes_array


def create_nodes(
    *, head_node: str, head_node_ip: str, port: str, nodes_array: list[str], temp_dir: str = None
) -> None:
    """
    Creates head + worker nodes.

    Parameters
    ----------
    head_node: str
        Head node ID/name
    head_node_ip: str
        Valid IPv4 address of head node
    port: str
        Port number
    nodes_array: Optional[list[str]], optional
        List of all available nodes
    temp_dir: Optional[str], optional
        Path to use for temporary dir

    """
    ip_head = f"{head_node_ip}:{port}"

    cmd = [
        "srun",
        "--nodes=1",
        "--ntasks=1",
        "-w",
        head_node,
        "ray",
        "start",
        "--head",
        f"--node-ip-address={head_node_ip}",
        f"--port={port}",
        "--block",
        "--include-dashboard=true",
        "--dashboard-host=0.0.0.0",
        "--dashboard-port=8080",
    ]

    if temp_dir is not None:
        cmd.append(f"--temp-dir={temp_dir}")

    subprocess.Popen(cmd)
    sleep(10)

    # number of nodes other than the head node
    num_nodes = len(nodes_array)

    # launch worker nodes
    for i in range(1, num_nodes):
        node_i = nodes_array[i]
        cmd_node = [
            "srun",
            "--nodes=1",
            "--ntasks=1",
            "-w",
            node_i,
            "ray",
            "start",
            "--address",
            ip_head,
            "--block",
        ]

        if temp_dir is not None:
            cmd_node.append(f"--temp-dir={temp_dir}")

        subprocess.Popen(cmd_node)
        sleep(5)


def create_cluster(temp_dir: Optional[str] = None) -> str:
    """Creates a Ray cluster on SLURM and returns IP address of its head node."""
    set_rlimit()
    head_node, head_node_ip, port, nodes_array = setup_head_node()
    create_nodes(
        head_node=head_node,
        head_node_ip=head_node_ip,
        port=port,
        nodes_array=nodes_array,
        temp_dir=temp_dir,
    )
    assert validIPAddress(head_node_ip) != "Invalid"
    return head_node_ip


def get_ray_res(keys: List[str]) -> List[Any]:
    compute_resources = ray.cluster_resources()
    return [compute_resources.get(key) for key in keys]


def initialize_ray_res(exec_req: ExecReq, logger: Optional[logging.Logger] = None) -> None:
    exec_req = ExecReq.model_validate(exec_req)

    if hasattr(exec_req, "compute_req"):
        num_cpus = getattr(exec_req.compute_req, "num_cpus", None)
        num_gpus = getattr(exec_req.compute_req, "num_gpus", None)
        object_store_memory = getattr(exec_req.compute_req, "object_store_memory", None)
    else:
        num_cpus = None
        num_gpus = None
        object_store_memory = None

    if exec_req.address:
        if logger:  # pragma: no cover
            logger.infof(
                "Attaching to Ray cluster at head node {exec_req}", exec_req=exec_req.address
            )
        ray.init(
            address="auto",
            _node_ip_address=exec_req.address,
            num_cpus=num_cpus,
            num_gpus=num_gpus,
            object_store_memory=object_store_memory,
        )
    else:
        ray.init(num_cpus=num_cpus, num_gpus=num_gpus, object_store_memory=object_store_memory)
        if logger:  # pragma: no cover
            logger.infof(
                "Creating Ray cluster using {num_cpus} cpus and {num_gpus} gpus.",
                num_cpus=num_cpus or "all available",
                num_gpus=num_gpus or "all available",
            )


def initialize_ray(
    logger: Optional[logging.Logger] = None, exec_req: Optional[ExecReq] = None
) -> tuple[int, int]:
    if ray.is_initialized():
        if logger:
            logger.info("Ray already initialized. Nothing to do ...")
        return get_ray_res(["CPU", "GPU"])

    if exec_req is None:
        if logger:  # pragma: no cover
            logger.info(
                "Creating Ray cluster with default settings and utilizing all available resources"
            )
        ray.init()
    else:
        initialize_ray_res(exec_req, logger)

    if not ray.is_initialized():
        raise RuntimeError("Ray was not properly initialized.")

    return get_ray_res(["CPU", "GPU"])
