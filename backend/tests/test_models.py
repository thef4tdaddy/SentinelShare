from datetime import datetime, timezone

import pytest
from backend.models import (GlobalSettings, ManualRule, Preference,
                            ProcessedEmail, Stats)
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool


@pytest.fixture(name="session")
def session_fixture():
    """Create an in-memory database for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


class TestProcessedEmail:

    def test_create_processed_email(self, session: Session):
        """Test creating a ProcessedEmail instance"""
        email = ProcessedEmail(
            email_id="test123@example.com",
            subject="Test Email",
            sender="sender@example.com",
            received_at=datetime.now(timezone.utc),
            status="forwarded",
            category="amazon",
            amount=50.00,
            reason="Detected as receipt",
        )

        session.add(email)
        session.commit()
        session.refresh(email)

        assert email.id is not None
        assert email.email_id == "test123@example.com"
        assert email.subject == "Test Email"
        assert email.sender == "sender@example.com"
        assert email.status == "forwarded"
        assert email.category == "amazon"
        assert email.amount == 50.00
        assert email.reason == "Detected as receipt"

    def test_processed_email_unique_email_id(self, session: Session):
        """Test that email_id must be unique"""
        from sqlalchemy.exc import IntegrityError

        email1 = ProcessedEmail(
            email_id="duplicate@example.com",
            subject="Email 1",
            sender="sender@example.com",
            received_at=datetime.now(timezone.utc),
            status="forwarded",
        )
        session.add(email1)
        session.commit()

        # Try to add another with same email_id
        email2 = ProcessedEmail(
            email_id="duplicate@example.com",
            subject="Email 2",
            sender="sender@example.com",
            received_at=datetime.now(timezone.utc),
            status="forwarded",
        )
        session.add(email2)

        with pytest.raises(IntegrityError):  # Should raise integrity error
            session.commit()

    def test_processed_email_default_processed_at(self, session: Session):
        """Test that processed_at has a default value"""
        email = ProcessedEmail(
            email_id="test@example.com",
            subject="Test",
            sender="sender@example.com",
            received_at=datetime.now(timezone.utc),
            status="forwarded",
        )

        session.add(email)
        session.commit()
        session.refresh(email)

        assert email.processed_at is not None
        assert isinstance(email.processed_at, datetime)

    def test_processed_email_optional_fields(self, session: Session):
        """Test that optional fields can be None"""
        email = ProcessedEmail(
            email_id="minimal@example.com",
            subject="Minimal Email",
            sender="sender@example.com",
            received_at=datetime.now(timezone.utc),
            status="ignored",
        )

        session.add(email)
        session.commit()
        session.refresh(email)

        assert email.category is None
        assert email.amount is None
        assert email.reason is None


class TestStats:

    def test_create_stats(self, session: Session):
        """Test creating a Stats instance"""
        stats = Stats(
            forwarded_count=10, blocked_count=5, total_amount_processed=150.50
        )

        session.add(stats)
        session.commit()
        session.refresh(stats)

        assert stats.id is not None
        assert stats.forwarded_count == 10
        assert stats.blocked_count == 5
        assert stats.total_amount_processed == 150.50
        assert stats.date is not None

    def test_stats_default_values(self, session: Session):
        """Test that Stats fields have correct default values"""
        stats = Stats()

        session.add(stats)
        session.commit()
        session.refresh(stats)

        assert stats.forwarded_count == 0
        assert stats.blocked_count == 0
        assert stats.total_amount_processed == 0.0
        assert stats.date is not None


class TestGlobalSettings:

    def test_create_global_setting(self, session: Session):
        """Test creating a GlobalSettings instance"""
        setting = GlobalSettings(
            key="poll_interval", value="60", description="Minutes between email polls"
        )

        session.add(setting)
        session.commit()
        session.refresh(setting)

        assert setting.id is not None
        assert setting.key == "poll_interval"
        assert setting.value == "60"
        assert setting.description == "Minutes between email polls"

    def test_global_setting_unique_key(self, session: Session):
        """Test that key must be unique"""
        from sqlalchemy.exc import IntegrityError

        setting1 = GlobalSettings(key="test_key", value="value1")
        session.add(setting1)
        session.commit()

        setting2 = GlobalSettings(key="test_key", value="value2")
        session.add(setting2)

        with pytest.raises(IntegrityError):  # Should raise integrity error
            session.commit()


class TestPreference:

    def test_create_preference(self, session: Session):
        """Test creating a Preference instance"""
        pref = Preference(item="amazon", type="Always Forward")

        session.add(pref)
        session.commit()
        session.refresh(pref)

        assert pref.id is not None
        assert pref.item == "amazon"
        assert pref.type == "Always Forward"
        assert pref.created_at is not None

    def test_preference_types(self, session: Session):
        """Test different preference types"""
        pref1 = Preference(item="spam@example.com", type="Blocked Sender")
        pref2 = Preference(item="promotions", type="Blocked Category")
        pref3 = Preference(item="paypal", type="Always Forward")

        session.add(pref1)
        session.add(pref2)
        session.add(pref3)
        session.commit()

        prefs = session.exec(select(Preference)).all()
        assert len(prefs) == 3


class TestManualRule:

    def test_create_manual_rule(self, session: Session):
        """Test creating a ManualRule instance"""
        rule = ManualRule(
            email_pattern="*@spam.com",
            subject_pattern="URGENT*",
            priority=5,
            purpose="Block spam emails",
        )

        session.add(rule)
        session.commit()
        session.refresh(rule)

        assert rule.id is not None
        assert rule.email_pattern == "*@spam.com"
        assert rule.subject_pattern == "URGENT*"
        assert rule.priority == 5
        assert rule.purpose == "Block spam emails"
        assert rule.created_at is not None

    def test_manual_rule_default_priority(self, session: Session):
        """Test that priority has default value"""
        rule = ManualRule(email_pattern="test@test.com")

        session.add(rule)
        session.commit()
        session.refresh(rule)

        assert rule.priority == 10

    def test_manual_rule_optional_fields(self, session: Session):
        """Test that pattern fields can be None"""
        rule = ManualRule(email_pattern="*@spam.com", priority=5)

        session.add(rule)
        session.commit()
        session.refresh(rule)

        assert rule.email_pattern == "*@spam.com"
        assert rule.subject_pattern is None
        assert rule.purpose is None

    def test_query_rules_by_priority(self, session: Session):
        """Test querying rules ordered by priority"""
        rule1 = ManualRule(email_pattern="low@test.com", priority=20)
        rule2 = ManualRule(email_pattern="high@test.com", priority=1)
        rule3 = ManualRule(email_pattern="medium@test.com", priority=10)

        session.add(rule1)
        session.add(rule2)
        session.add(rule3)
        session.commit()

        rules = session.exec(select(ManualRule).order_by(ManualRule.priority)).all()  # type: ignore

        assert len(rules) == 3
        assert rules[0].priority == 1
        assert rules[1].priority == 10
        assert rules[2].priority == 20
