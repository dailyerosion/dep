"""Test io/wepp.py"""

import datetime
import os

from pydep.io.wepp import (
    intensity,
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


def test_intensity_rounding():
    """Test we can handle time resolution pain."""
    times = [5.73, 23.9667, 23.9833]
    points = [0.0, 12.62, 14.0]
    res = intensity(times, points, [10, 20])
    assert abs(res["i10_mm"] - 1.48) < 0.01
    assert abs(res["i20_mm"] - 1.6) < 0.01


def test_intensity():
    """Test basic intensity calculations."""
    times = [0.5, 1.5]
    points = [0, 10]
    res = intensity(times, points, [10, 20])
    assert abs(res["i10_mm"] - 10 / 6.0) < 0.01
    assert abs(res["i20_mm"] - 10 / 3.0) < 0.01


def test_intensity2():
    """Test intensity calculations."""
    times = [0.5, 1.5, 2.0]
    points = [0, 10, 20]
    res = intensity(times, points, [10, 20])
    assert abs(res["i10_mm"] - 10 / 3.0) < 0.01
    assert abs(res["i20_mm"] - 10 / 1.5) < 0.01


def test_crop():
    """Read a crop file."""
    df = read_crop(get_path("crop.txt"))
    assert len(df.index) > 10
    assert abs(df["lai"].max() - 9.00) < 0.01
    assert abs(df["avg_temp_c"].max() - 24.30) < 0.01


def test_reading_depenv():
    """We should be backwards compatible with DEP files."""
    df = read_env(get_path("env_year4_dep.txt"))
    assert df["date"].max().year == 2023


def test_empty():
    """don't error out on an empty ENV"""
    df = read_env(get_path("empty_env.txt"))
    assert df.empty


def test_gh183_env_year4():
    """Test reading an env file with a four digit year."""
    df = read_env(get_path("env_year4.txt"))
    assert df["date"].max().year == 2023


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
    df = read_cli(get_path("cli.txt"), compute_intensity_over=[80, 120])
    assert len(df.index) == 4018
    assert (df["i80_mm"].max() - 51.12) < 0.01


def test_cli_rfactor():
    """read a CLI file please"""
    df = read_cli(get_path("cli.txt"), compute_rfactor=True)
    assert abs(df["rfactor"].max() - 872.63) < 0.01
    assert (df.groupby(df.index.year).sum()["rfactor"].max() - 4276.60) < 0.01


def test_slp():
    """Read a slope file"""
    slp = read_slp(get_path("slp.txt"))
    assert len(slp) == 2
    assert abs(slp[1]["y"][-1] + 10.34) < 0.01
    assert abs(slp[1]["slopes"][-1] - 0.064) < 0.01


def test_ofe():
    """Read an OFE please"""
    df = read_ofe(get_path("ofe.txt"))
    assert abs(df["precip"].max() - 107.56) < 0.01

    df = read_ofe(get_path("ofe2.txt"))
    print(df["sedleave"].sum())
    assert abs(df["sedleave"].sum() - 400257.48) < 0.01
