"""Test dailyersoion.workflows.importer."""

import pandas as pd

from dailyerosion.workflows.importer import clean_water_landuse


def test_clean_water_landuse():
    """Test the rectifying of the T values."""
    df = pd.DataFrame(
        {
            "landuse": [
                "TTTTTTTT",
                "TCBCBCBC",
                "TTCBCBCC",
                "CCCCCCCC",
                "TTTTTTTC",
                "CBCBTBBB",
            ],
        }
    )
    clean_water_landuse(df)
    answer = [
        "TTTTTTTT",
        "CCBCBCBC",
        "CCCBCBCC",
        "CCCCCCCC",
        "TTTTTTTT",
        "CBCBBBBB",
    ]
    assert df["landuse"].tolist() == answer
