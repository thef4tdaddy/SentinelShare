"""
Tests for routers/__init__.py

This test ensures the routers package can be imported successfully.
Even though the __init__.py is empty, explicit tests help with coverage tracking.
"""

import sys


def test_routers_package_import():
    """Test that the routers package can be imported and exists as a module."""
    import backend.routers  # noqa: F401
    assert "backend.routers" in sys.modules
    assert hasattr(backend.routers, "__file__")
