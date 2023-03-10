"""test pydep.util"""

import pytest
from pydep import util


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
