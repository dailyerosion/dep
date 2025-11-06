"""Test pydep.workflows.wepprun module."""

from pydep.workflows.wepprun import (
    WeppJobPayload,
    WeppRunConfig,
    build_runfile,
)


def test_build_runfile():
    """Test the building of a runfile."""
    config = WeppRunConfig(years=18, irrigation=2)
    runfile = build_runfile(config, "", "", "", "")
    assert "18\n" in runfile


def test_weppjobpayload_valid():
    """Test WeppJobPayload with valid data."""
    runfile = "E\nYes\n1\n1\nNo\n1\nNo\n/dev/null\n"
    payload = WeppJobPayload(
        wepprun=runfile,
        weppexe="wepp20240930",
        errorfn="/tmp/error",
    )
    assert payload.wepprun == runfile
    assert payload.weppexe == "wepp20240930"
