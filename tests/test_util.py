"""test pydep.util"""

import logging

import pytest
from pyiem.database import get_dbconnc
from pyiem.iemre import SOUTH, WEST

from pydep import util


def test_tqdm_logger_with_invalid_record(caplog):
    """Test what happens when we log something unlogable."""
    log = util.tqdm_logger()
    with caplog.at_level(logging.INFO):
        log.warning("Test message")
    assert "Test message" in caplog.text


def test_tqdm_logger(caplog: pytest.LogCaptureFixture):
    """Test the logger."""
    log = util.tqdm_logger()
    with caplog.at_level(logging.INFO):
        log.warning("Test message")
    assert "Test message" in caplog.text


def test_logger(caplog: pytest.LogCaptureFixture):
    """Test the logger."""
    log = util.logger()
    with caplog.at_level(logging.INFO):
        log.warning("Test message")
    assert "Test message" in caplog.text


def test_compute_management_for_groupid():
    """Test scenarios."""
    assert util.compute_management_for_groupid("0000") == "0"
    assert util.compute_management_for_groupid("1000") == "1"
    assert util.compute_management_for_groupid("0001") == "1"


def test_kwfact_class():
    """Test kwfact classification."""
    assert util.get_kwfact_class(0) == 1
    assert util.get_kwfact_class(0.28) == 1
    assert util.get_kwfact_class(0.33) == 3


def test_slope_class():
    """Test slope classification."""
    assert util.get_slope_class(0) == 1
    assert util.get_slope_class(2) == 1
    assert util.get_slope_class(100) == 5


def test_clear_huc12data():
    """Can we clear data?"""
    dbconn, cursor = get_dbconnc("idep")
    util.clear_huc12data(cursor, "123456789012", 0)
    cursor.close()
    dbconn.close()


def test_cli_fname_non_us():
    """Test non-US climate file names."""
    res = util.get_cli_fname(100.01, 42.5, 0)
    assert res == "/mnt/dep/china/2/0/cli/E100xN42/E100.01xN42.50.cli"
    res = util.get_cli_fname(19.99, 42.49, 0)
    assert res == "/mnt/dep/europe/2/0/cli/E019xN42/E019.99xN42.49.cli"
    res = util.get_cli_fname(-60.55, -42.5, 0)
    assert res == "/mnt/dep/sa/2/0/cli/W060xS42/W060.55xS42.50.cli"


def test_cli_fname():
    """Do we get the right climate file names?"""
    res = util.get_cli_fname(-95.5, 42.5, 0)
    assert res == "/i/0/cli/095x042/095.50x042.50.cli"
    res = util.get_cli_fname(-97.9999, 42.0, 0)
    assert res == "/i/0/cli/098x042/098.00x042.00.cli"


def test_cli_fname_raises():
    """Test out of bounds requests."""
    with pytest.raises(ValueError):
        util.get_cli_fname(WEST - 1, SOUTH + 1)
    with pytest.raises(ValueError):
        util.get_cli_fname(WEST + 1, SOUTH - 1)


def test_scenarios():
    """Can we load scenarios?"""
    df = util.load_scenarios()
    assert not df.empty
    assert 0 in df.index
