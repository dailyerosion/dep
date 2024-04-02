"""Test pydep.tillage."""

from pydep import tillage


def test_simple():
    """Test import of API."""
    plants = ["C", "B", "W", "P"]
    cfactors = list(range(1, 7))
    zones = ["IA_NORTH", "IA_SOUTH", "KS_NORTH"]
    for bp in plants:
        for pp in plants:
            for ap in plants:
                for cfactor in cfactors:
                    for zone in zones:
                        res = tillage.make_tillage(
                            0, zone, bp, pp, ap, cfactor, 1
                        )
                        assert res is not None


def test_unknown_file():
    """Test unknown file."""
    res = tillage.make_tillage(0, "IA_NORTH", "q", "q", "q", 1, 1)
    assert res == ""
