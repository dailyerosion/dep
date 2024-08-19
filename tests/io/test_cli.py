"""Test pydep.io.cli stuff."""

from datetime import date

from pydep.io.cli import (
    BOUNDS,
    check_has_clifiles,
    compute_tile_bounds,
    daily_formatter,
)


def test_compute_bounds():
    """Test that we compute bounds properly."""
    res = compute_tile_bounds(1, 1, domain="")
    assert res == BOUNDS(south=28, north=33, east=-116, west=-121)


def test_has_clifiles():
    """Test our check for clifiles."""
    bnds = BOUNDS(south=41, north=43, east=-99, west=-101)
    assert check_has_clifiles(bnds)
    bnds = BOUNDS(south=11, north=13, east=-97, west=-98)
    assert not check_has_clifiles(bnds)


def test_daily_formatter():
    """Test our formatter for ugilness."""
    res = daily_formatter(
        date(2023, 4, 17),
        [],
        -0.01,
        -0.01,
        10,
        40,
        -0.01,
    )
    ans = "17\t4\t2023\t0\t0.0\t0.0\t10\t40.0\t0\t0.0\n"
    assert res == ans
