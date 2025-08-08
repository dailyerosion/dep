"""Test workflows.clifile module.

The akrherz/iem-database repo has the "pump primed" with a number of things
ready to go in order to process 2vi  Jan 2017.

1. A climate file at 42.99N -96.01W with path /tmp/096.01x42.99.cli

"""

import re
from datetime import date, timedelta

import pytest
from pyiem.util import utc
from pytest_httpx import HTTPXMock

from pydep.io.wepp import read_cli
from pydep.workflows.clifile import (
    CLIFileWorkflowFailure,
    daily_editor_workflow,
    get_sts_ets_at_localhour,
    preflight_check,
)

DUMMY_SCENARIO = -1


def test_preflight_check_future():
    """Test that this returns false for a future date."""
    assert not preflight_check(date.today() + timedelta(days=10), "china")


def test_preflight_nodata():
    """Test a request that should get empty data response."""
    assert not preflight_check(date(1880, 1, 1), "china")


def test_get_sts_ets_at_localhour():
    """Test that we can compute the start and end times for a domain date."""
    sts, ets = get_sts_ets_at_localhour("", date(2017, 1, 2), 0)
    assert sts == utc(2017, 1, 2, 6)
    assert ets == utc(2017, 1, 3, 6)
    sts, ets = get_sts_ets_at_localhour("china", date(2017, 1, 2), 0)
    assert sts == utc(2017, 1, 1, 16)
    assert ets == utc(2017, 1, 2, 16)
    sts, ets = get_sts_ets_at_localhour("europe", date(2017, 1, 2), 0)
    assert sts == utc(2017, 1, 1, 23)
    assert ets == utc(2017, 1, 2, 23)
    sts, ets = get_sts_ets_at_localhour("sa", date(2017, 1, 2), 0)
    assert sts == utc(2017, 1, 2, 2)
    assert ets == utc(2017, 1, 3, 2)


def test_noclifiles():
    """Test that no climate files are found for this tile."""
    assert (
        daily_editor_workflow(
            DUMMY_SCENARIO,
            "",
            date(2017, 1, 1),
            -101,
            -100,
            88,
            89,
        )[1]
        == 0
    )


def test_bad_iemre():
    """Test that no climate files are found for this tile."""
    # We should not need to mock any web requests as the failure should
    # happen immediately
    with pytest.raises(CLIFileWorkflowFailure) as excinfo:
        daily_editor_workflow(
            DUMMY_SCENARIO,
            "",
            date(2017, 1, 2),
            -96,
            -95,
            43,
            44,
        )
    assert "IEMRE data out of bounds!" in str(excinfo.value)


def test_china_no_iemre_data():
    """Test IEMRE failure with no data."""
    with pytest.raises(CLIFileWorkflowFailure) as excinfo:
        daily_editor_workflow(
            DUMMY_SCENARIO,
            "china",
            date(2025, 7, 22),
            89,
            94,
            38,
            43,
        )
    assert "high_tmpk" in str(excinfo.value)


def test_china():
    """Test the non-US domain code."""
    daily_editor_workflow(
        DUMMY_SCENARIO,
        "china",
        date(2025, 7, 21),
        89,
        94,
        38,
        43,
    )
    clidf = read_cli("/tmp/E092.80xN39.30.cli")
    assert abs(clidf.at["2025-07-21", "pcpn"] - 0.0) < 0.01


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
        "",
        date(2017, 1, 2),
        -101,
        -96,
        38,
        43,
    )
    clidf = read_cli("/tmp/096.01x42.99.cli")
    assert abs(clidf.at["2017-01-02", "pcpn"] - 331.5) < 0.01
