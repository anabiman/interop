[![Build Status](https://dev.azure.com/dcimds/MDS_Demo_Platform/_apis/build/status%2Ftesting?branchName=main)](https://dev.azure.com/dcimds/MDS_Demo_Platform/_build/latest?definitionId=17&branchName=main)

interop
########################################################################

Documentation
=============

`View the interop docs here
<https://devdocs...net/gh/interop>`_.

Installation
============

interop can be installed with `conda <https://conda.io>`_.

We suggest using `mamba <https://github.com/mamba-org/mamba>`_, an optimized conda package solver,
for installing packages. Install mamba with ``conda install -n base mamba``.

Connect to the the VPN and install interop with::

    mamba install \
      --override-channels --strict-channel-priority \
      -c https://conda.prod...dev -c conda-forge \
      interop


Contributing Guide
==================

For information on setting up interop for development and
contributing changes, view `CONTRIBUTING.rst <CONTRIBUTING.rst>`_.
