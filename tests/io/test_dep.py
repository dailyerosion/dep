"""Test reading pydep.io.dep stuff."""

import os

from pydep.io.dep import read_env, read_wb


def test_empty():
    """don't error out on an empty ENV"""
    df = read_env(get_path("empty_env.txt"))
    assert df.empty


def test_gh183_env_year4():
    """Test reading an env file with a four digit year."""
    df = read_env(get_path("env_year4_dep.txt"))
    assert df["date"].max().year == 2023


def get_path(name):
    """helper"""
    basedir = os.path.dirname(__file__)
    return os.path.join(basedir, "..", "data", name)


def test_wb():
    """read a WB file please"""
    df = read_wb(get_path("wb.txt"))
    assert abs(df["precip"].max() - 162.04) < 0.01
