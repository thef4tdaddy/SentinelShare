"""
Tests for routers/__init__.py

This test ensures the routers package can be imported successfully.
Even though the __init__.py is empty, explicit tests help with coverage tracking.
"""


def test_routers_package_import():
    """Test that the routers package can be imported."""
    try:
        import backend.routers

        assert backend.routers is not None
    except ImportError as e:
        pytest.fail(f"Failed to import backend.routers: {e}")


def test_routers_package_exists():
    """Test that the routers package exists as a module."""
    import sys

    import backend.routers

    assert "backend.routers" in sys.modules
    assert hasattr(backend.routers, "__file__")
