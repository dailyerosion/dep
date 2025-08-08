"""Importable."""

import logging
import os
from importlib.metadata import PackageNotFoundError, version

# Create a default logger instance to be used within package
LOG = logging.getLogger(__name__)

try:
    __version__ = version(__name__)
    pkgdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    if not pkgdir.endswith("site-packages"):
        __version__ += "-dev"
except PackageNotFoundError:
    # package is not installed
    __version__ = "dev"
