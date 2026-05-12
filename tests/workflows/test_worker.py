"""Test dailyerosion worker."""

import pytest

from dailyerosion.workflows.worker import sanitize_exe


def test_ok():
    """Test something that is allowed."""
    # resolve mucks the potential symlink of /opt/dep
    assert sanitize_exe("/opt/dep/bin/sweep").endswith("sweep")


def test_invalid():
    """Test that we stop this."""
    with pytest.raises(ValueError):
        sanitize_exe("/etc/passwd")
