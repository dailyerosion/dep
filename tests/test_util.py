"""test pydep.util"""

import pytest
from pydep import util
from pyiem.database import get_dbconnc


def test_clear_huc12data():
    """Can we clear data?"""
    dbconn, cursor = get_dbconnc("idep")
    util.clear_huc12data(cursor, "123456789012", 0)
    cursor.close()
    dbconn.close()


def test_cli_fname():
    """Do we get the right climate file names?"""
    res = util.get_cli_fname(-95.5, 42.5, 0)
    assert res == "/i/0/cli/095x042/095.50x042.50.cli"
    res = util.get_cli_fname(-97.9999, 42.0, 0)
    assert res == "/i/0/cli/098x042/098.00x042.00.cli"


def test_cli_fname_raises():
    """Test out of bounds requests."""
    with pytest.raises(ValueError):
        util.get_cli_fname(util.WEST - 1, util.SOUTH + 1)
    with pytest.raises(ValueError):
        util.get_cli_fname(util.WEST + 1, util.SOUTH - 1)


def test_scenarios():
    """Can we load scenarios?"""
    df = util.load_scenarios()
    assert not df.empty
    assert 0 in df.index
