"""Test workflows.clifile module.

The akrherz/iem-database repo has the "pump primed" with a number of things
ready to go in order to process 2vi  Jan 2017.

1. A climate file at 42.99N -96.01W with path /tmp/096.01x42.99.cli

"""

import re
from datetime import date

from pytest_httpx import HTTPXMock

from pydep.io.wepp import read_cli
from pydep.workflows.clifile import (
    daily_editor_workflow,
)

DUMMY_SCENARIO = -1


def test_noclifiles():
    """Test that no climate files are found for this tile."""
    assert (
        daily_editor_workflow(
            DUMMY_SCENARIO,
            date(2017, 1, 1),
            -101,
            -100,
            88,
            89,
        )
        == 0
    )


def test_faked_stage4(httpx_mock: HTTPXMock):
    """CI provides some faked data for 2 Jan 2017."""
    with open("tests/data/a2m_201701020000.png", "rb") as fh:
        content = fh.read()
    with open("tests/data/n0r_201701010025.png", "rb") as fh:
        n0r_content = fh.read()
    httpx_mock.add_response(
        content=content, url=re.compile(".*mrms.*"), is_reusable=True
    )
    # Presently, MRMS will fail as there are too many zeros where there is
    # lots of faked data within stage IV, so n0r requests get generated.
    httpx_mock.add_response(
        content=n0r_content, url=re.compile(".*n0r.*"), is_reusable=True
    )
    daily_editor_workflow(
        DUMMY_SCENARIO,
        date(2017, 1, 2),
        -101,
        -96,
        38,
        43,
    )
    clidf = read_cli("/tmp/096.01x42.99.cli")
    assert abs(clidf.at["2017-01-02", "pcpn"] - 331.5) < 0.01
