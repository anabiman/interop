Installation
============

interop can be installed with `conda <https://conda.io>`__.

We suggest using `mamba <https://github.com/mamba-org/mamba>`__, an optimized conda package solver,
for installing packages. Install mamba with ``conda install -n base mamba``.

Connect to the the VPN and install interop with::

    mamba install \
      --override-channels --strict-channel-priority \
      -c https://conda.prod.dci.dev -c conda-forge \
      interop
