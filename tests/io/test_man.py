"""Test management reading."""
import os

from pydep.io.man import man2df, read_man


def get_path(name):
    """helper"""
    basedir = os.path.dirname(__file__)
    return os.path.join(basedir, "..", "data", name)


def test_230511_man2df_index_error():
    """Fix a index error found."""
    df = man2df(read_man(get_path("man4.txt")))
    assert len(df.index) == 17


def test_man_rotation_repeats():
    """Test that a management file can have a rotation repeat read."""
    manfile = read_man(get_path("man3.txt"))
    assert manfile["nrots"] == 2
    assert manfile["nyears"] == 14
    assert len(manfile["rotations"]) == 28


def test_man():
    """Read a management file please"""
    manfile = read_man(get_path("man.txt"))
    assert manfile["nop"] == 5
    assert manfile["nini"] == 2
    assert manfile["nsurf"] == 2
    assert manfile["nwsofe"] == 3
    assert manfile["nrots"] == 1
    assert manfile["nyears"] == 11

    manfile = read_man(get_path("man2.txt"))
    assert manfile["nop"] == 0


def test_man2df():
    """Test generation of DataFrame from management file."""
    mandict = read_man(get_path("man3.txt"))
    df = man2df(mandict)
    ans = "Soy_2194"
    assert df.query("year == 6 and ofe == 1").iloc[0]["crop_name"] == ans
    df = man2df(mandict, year1=2007)
    assert df.query("year == 2012 and ofe == 1").iloc[0]["crop_name"] == ans
