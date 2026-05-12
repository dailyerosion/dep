"""Common utilities for DEP queue workers."""

from pathlib import Path


def sanitize_exe(exe: str) -> str:
    """Reduce the blast radius of the naughty things that could come in.

    Enforces:
      - Filename has either `weps`, `sweep`, or `wepp` in the name
    """
    exe_path = Path(exe).resolve()
    allowed = ["weps", "sweep", "wepp"]
    if not any(keyword in exe_path.name for keyword in allowed):
        raise ValueError(f"Invalid executable name: {exe}")
    return str(exe_path)
