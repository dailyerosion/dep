"""Test pydep.io.cli stuff."""

from datetime import date

from pydep.io.cli import daily_formatter


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
