#! /bin/sh

version=$(python -c "import interop; print(interop.__version__)")
use_conda=false

if $use_conda ; then
    pkg_manager="conda"
else
    pkg_manager="poetry"
fi

podman build -t interop/$pkg_manager/$version \
       --file dockerfile
