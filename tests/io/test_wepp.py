"""Test io/wepp.py"""
import datetime
import os

from pydep.io.wepp import (
    read_cli,
    read_crop,
    read_env,
    read_ofe,
    read_slp,
    read_yld,
)


def get_path(name):
    """helper"""
    basedir = os.path.dirname(__file__)
    return os.path.join(basedir, "..", "data", name)


def test_crop():
    """Read a crop file."""
    df = read_crop(get_path("crop.txt"))
    assert len(df.index) > 10
    assert abs(df["lai"].max() - 9.00) < 0.01
    assert abs(df["avg_temp_c"].max() - 24.30) < 0.01


def test_empty():
    """don't error out on an empty ENV"""
    df = read_env(get_path("empty_env.txt"))
    assert df.empty


def test_read():
    """Read a ENV file"""
    df = read_env(get_path("good_env.txt"))
    df2 = df[df["date"] == datetime.datetime(2010, 6, 5)]
    assert len(df2.index) == 1
    row = df2.iloc[0]
    assert row["runoff"] == 86.3


def test_yld():
    """Read a slope file"""
    df = read_yld(get_path("yld.txt"))
    assert len(df.index) == 10
    assert abs(df["yield_kgm2"].max() - 0.93) < 0.01


def test_cli():
    """read a CLI file please"""
    df = read_cli(get_path("cli.txt"))
    assert len(df.index) == 4018


def test_cli_rfactor():
    """read a CLI file please"""
    df = read_cli(get_path("cli.txt"), compute_rfactor=True)
    assert abs(df["rfactor"].max() - 872.63) < 0.01
    assert (df.groupby(df.index.year).sum()["rfactor"].max() - 4276.60) < 0.01


def test_slp():
    """Read a slope file"""
    slp = read_slp(get_path("slp.txt"))
    assert len(slp) == 5
    assert abs(slp[4]["y"][-1] + 2.91) < 0.01
    assert abs(slp[4]["slopes"][-1] - 0.033) < 0.01


def test_ofe():
    """Read an OFE please"""
    df = read_ofe(get_path("ofe.txt"))
    assert abs(df["precip"].max() - 107.56) < 0.01

    df = read_ofe(get_path("ofe2.txt"))
    print(df["sedleave"].sum())
    assert abs(df["sedleave"].sum() - 400257.48) < 0.01
