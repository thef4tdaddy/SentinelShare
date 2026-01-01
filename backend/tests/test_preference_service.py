"""Tests for PreferenceService."""

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from backend.models import Preference
from backend.services.preference_service import PreferenceService


@pytest.fixture(name="engine")
def engine_fixture():
    """Create an in-memory database engine for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="session")
def session_fixture(engine):
    """Create a database session for testing."""
    with Session(engine) as session:
        yield session


@pytest.fixture(name="sample_preferences")
def sample_preferences_fixture(session):
    """Create sample preferences for testing."""
    prefs = [
        Preference(item="spam@example.com", type="Blocked Sender"),
        Preference(item="newsletter@bad.com", type="Blocked Sender"),
        Preference(item="receipts@store.com", type="Always Forward"),
        Preference(item="bills@utility.com", type="Always Forward"),
        Preference(item="restaurants", type="Blocked Category"),
    ]
    for pref in prefs:
        session.add(pref)
    session.commit()
    return prefs


class TestPreferenceService:
    """Test suite for PreferenceService."""

    def test_get_preferences_by_types(self, session, sample_preferences):
        """Test getting preferences filtered by type."""
        result = PreferenceService.get_preferences_by_types(
            session, ["Blocked Sender", "Always Forward"]
        )

        assert len(result) == 4  # 2 blocked + 2 allowed
        types = [p.type for p in result]
        assert "Blocked Sender" in types
        assert "Always Forward" in types
        assert "Blocked Category" not in types

    def test_get_preferences_by_types_single(self, session, sample_preferences):
        """Test getting preferences with single type filter."""
        result = PreferenceService.get_preferences_by_types(session, ["Blocked Sender"])

        assert len(result) == 2
        assert all(p.type == "Blocked Sender" for p in result)

    def test_get_preferences_dict(self, session, sample_preferences):
        """Test getting preferences organized by category."""
        result = PreferenceService.get_preferences_dict(session)

        assert "blocked" in result
        assert "allowed" in result
        assert len(result["blocked"]) == 2
        assert len(result["allowed"]) == 2
        assert "spam@example.com" in result["blocked"]
        assert "receipts@store.com" in result["allowed"]

    def test_get_preferences_dict_empty(self, session):
        """Test getting preferences when database is empty."""
        result = PreferenceService.get_preferences_dict(session)

        assert result == {"blocked": [], "allowed": []}

    def test_validate_preferences_success(self):
        """Test validation with valid preferences."""
        # Should not raise any exception
        PreferenceService.validate_preferences(
            blocked_senders=["spam@example.com", "bad@site.com"],
            allowed_senders=["receipts@store.com"],
        )

    def test_validate_preferences_duplicate_blocked(self):
        """Test validation catches duplicate blocked senders."""
        with pytest.raises(ValueError, match="Duplicate entries found in blocked"):
            PreferenceService.validate_preferences(
                blocked_senders=["spam@example.com", "spam@example.com"],
                allowed_senders=["receipts@store.com"],
            )

    def test_validate_preferences_duplicate_allowed(self):
        """Test validation catches duplicate allowed senders."""
        with pytest.raises(ValueError, match="Duplicate entries found in allowed"):
            PreferenceService.validate_preferences(
                blocked_senders=["spam@example.com"],
                allowed_senders=["receipts@store.com", "receipts@store.com"],
            )

    def test_validate_preferences_overlap(self):
        """Test validation catches overlap between blocked and allowed."""
        with pytest.raises(
            ValueError, match="Cannot have same item in both blocked and allowed"
        ):
            PreferenceService.validate_preferences(
                blocked_senders=["overlap@example.com", "spam@site.com"],
                allowed_senders=["receipts@store.com", "overlap@example.com"],
            )
