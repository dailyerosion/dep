"""Importable."""

import os
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pydep")
    pkgdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    if not pkgdir.endswith("site-packages"):
        __version__ += "-dev"
except PackageNotFoundError:
    # package is not installed
    __version__ = "dev"
