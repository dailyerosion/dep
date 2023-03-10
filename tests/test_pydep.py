"""test API."""

import pydep


def test_api():
    """Test import of API."""
    assert pydep.__version__ is not None
