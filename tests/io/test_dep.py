"""Test reading pydep.io.dep stuff."""
import os

from pydep.io.dep import read_wb


def get_path(name):
    """helper"""
    basedir = os.path.dirname(__file__)
    return os.path.join(basedir, "..", "data", name)


def test_wb():
    """read a WB file please"""
    df = read_wb(get_path("wb.txt"))
    assert abs(df["precip"].max() - 162.04) < 0.01
