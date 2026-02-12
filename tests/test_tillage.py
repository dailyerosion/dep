"""Test dailyerosion.tillage."""

from dailyerosion import tillage


def test_gh266_pasture():
    """Test that an initial planting operation is created."""
    res = tillage.make_tillage(0, "IA_NORTH", "P", "P", "P", 1, 1)
    assert "Plant-Perennial" in res


def test_simple():
    """Test import of API."""
    plants = ["C", "B", "W", "P", "G"]
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
