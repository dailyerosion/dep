"""Exercise our dynamic tillage mess."""

from datetime import date

import numpy as np
import pandas as pd
import pytest

from pydep.workflows.dyntillage import do_planting, do_tillage


@pytest.fixture
def fields() -> pd.DataFrame:
    """Return our test dataframe."""
    return pd.DataFrame(
        {
            "acres": np.ones(10) * 100,
            "crop": ["C"] * 5 + ["S"] * 5,
            "plant_needed": [True] * 10,
            "till_needed": [True] * 10,
            "till1": [date(2000, 7, 1)] * 10,  # Future means need
            "till2": [date(2000, 7, 1)] * 10,
            "till3": [date(2000, 7, 1)] * 10,
            "plant": [date(2000, 7, 1)] * 10,
            "operation_done": [False] * 10,
        },
    )


def test_mud_it_in(fields):
    """Test scenario with all fields that should get planted."""
    # No tillage needed
    fields["till_needed"] = False
    dt = date(2000, 6, 11)
    acres_planted = do_planting(fields, dt, True, 0)
    assert acres_planted == 1000.0


def test_mud_it_in_no_planting(fields):
    """Test scenario with all fields getting tilled, none should be planted."""
    dt = date(2000, 6, 11)
    acres_tilled = do_tillage(fields, dt, True, 0)
    assert acres_tilled == 1000.0
    acres_planted = do_planting(fields, dt, True, 0)
    assert acres_planted == 0.0


def test_no_soybeans_planted_before_season_starts(fields):
    """Test scenario with no soybeans planted, hopefully."""
    # Set everything to soybeans, ready to plant
    fields["crop"] = "S"
    fields["till_needed"] = False
    dt = date(2000, 4, 4)
    acres_planted = do_planting(fields, dt, False, 0)
    assert acres_planted == 0


def test_no_soybeans_planted_preferred_corn_fields(fields):
    """Test scenario with no soybeans planted, hopefully."""
    # No tillage needed
    fields["till_needed"] = False
    dt = date(2000, 4, 16)
    acres_planted = do_planting(fields, dt, False, 0)
    assert acres_planted == 100.0
    assert fields[fields["operation_done"]].iloc[0]["crop"] == "C"


def test_one_field_tilled(fields):
    """Should have one field tilled, nothing planted."""
    dt = date(2000, 5, 1)
    acres_tilled = do_tillage(fields, dt, False, 0)
    assert acres_tilled == 100.0
    assert fields[fields["operation_done"]].iloc[0]["till1"] == dt
