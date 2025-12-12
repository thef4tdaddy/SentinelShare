from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest
from backend.models import ManualRule, ProcessedEmail
from backend.routers import actions
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


@pytest.fixture(name="sample_ignored_email")
def sample_ignored_email_fixture(session: Session):
    """Create a sample ignored email for testing"""
    now = datetime.now(timezone.utc)
    
    email = ProcessedEmail(
        email_id="ignored-email@test.com",
        subject="Newsletter from Company",
        sender="newsletter@company.com",
        received_at=now - timedelta(minutes=30),
        processed_at=now - timedelta(minutes=30),
        status="ignored",
        account_email="user1@example.com",
        category=None,
        reason="Not a receipt",
    )
    session.add(email)
    session.commit()
    session.refresh(email)
    return email


class TestToggleIgnored:
    """Tests for the toggle-ignored endpoint"""
    
    def test_toggle_ignored_email_success(self, session: Session, sample_ignored_email):
        """Test successfully toggling an ignored email"""
        # Mock the EmailForwarder and environment
        with patch.dict('os.environ', {'WIFE_EMAIL': 'wife@example.com'}):
            with patch('backend.routers.actions.EmailForwarder.forward_email', return_value=True):
                # Call the endpoint
                request = actions.ToggleIgnoredRequest(email_id=sample_ignored_email.id)
                result = actions.toggle_ignored_email(request, session)
                
                # Check result
                assert result["success"] is True
                assert "Email forwarded and rule created" in result["message"]
                assert result["email"].status == "forwarded"
                assert result["email"].reason == "Manually toggled from ignored"
                
                # Check that email status was updated
                updated_email = session.get(ProcessedEmail, sample_ignored_email.id)
                assert updated_email.status == "forwarded"
                assert updated_email.reason == "Manually toggled from ignored"
                
                # Check that a manual rule was created
                rules = session.exec(select(ManualRule)).all()
                assert len(rules) == 1
                assert rules[0].email_pattern == "newsletter@company.com"
                assert "Auto-created from ignored email" in rules[0].purpose
    
    def test_toggle_ignored_email_with_formatted_sender(self, session: Session):
        """Test toggling an email with sender in 'Name <email>' format"""
        # Create email with formatted sender
        email = ProcessedEmail(
            email_id="formatted@test.com",
            subject="Test Email",
            sender="John Doe <john@example.com>",
            received_at=datetime.now(timezone.utc),
            processed_at=datetime.now(timezone.utc),
            status="ignored",
            account_email="user1@example.com",
            category=None,
            reason="Not a receipt",
        )
        session.add(email)
        session.commit()
        session.refresh(email)
        
        with patch.dict('os.environ', {'WIFE_EMAIL': 'wife@example.com'}):
            with patch('backend.routers.actions.EmailForwarder.forward_email', return_value=True):
                request = actions.ToggleIgnoredRequest(email_id=email.id)
                result = actions.toggle_ignored_email(request, session)
                
                assert result["success"] is True
                
                # Check that rule was created with extracted email
                rules = session.exec(select(ManualRule)).all()
                assert len(rules) == 1
                assert rules[0].email_pattern == "john@example.com"
    
    def test_toggle_ignored_email_not_found(self, session: Session):
        """Test toggling a non-existent email"""
        request = actions.ToggleIgnoredRequest(email_id=9999)
        
        with pytest.raises(Exception) as exc_info:
            actions.toggle_ignored_email(request, session)
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_toggle_non_ignored_email(self, session: Session):
        """Test toggling an email that is not ignored"""
        # Create a forwarded email
        email = ProcessedEmail(
            email_id="forwarded@test.com",
            subject="Test Email",
            sender="test@example.com",
            received_at=datetime.now(timezone.utc),
            processed_at=datetime.now(timezone.utc),
            status="forwarded",
            account_email="user1@example.com",
            category="shopping",
            reason="Detected as receipt",
        )
        session.add(email)
        session.commit()
        session.refresh(email)
        
        request = actions.ToggleIgnoredRequest(email_id=email.id)
        
        with pytest.raises(Exception) as exc_info:
            actions.toggle_ignored_email(request, session)
        
        assert "not 'ignored'" in str(exc_info.value)
    
    def test_toggle_ignored_email_forward_failure(self, session: Session, sample_ignored_email):
        """Test handling when email forwarding fails"""
        with patch.dict('os.environ', {'WIFE_EMAIL': 'wife@example.com'}):
            with patch('backend.routers.actions.EmailForwarder.forward_email', return_value=False):
                request = actions.ToggleIgnoredRequest(email_id=sample_ignored_email.id)
                
                with pytest.raises(Exception) as exc_info:
                    actions.toggle_ignored_email(request, session)
                
                assert "Failed to forward email" in str(exc_info.value)
                
                # Verify email status was not changed
                email = session.get(ProcessedEmail, sample_ignored_email.id)
                assert email.status == "ignored"
                
                # Verify no rule was created
                rules = session.exec(select(ManualRule)).all()
                assert len(rules) == 0
    
    def test_toggle_ignored_email_missing_wife_email(self, session: Session, sample_ignored_email):
        """Test handling when WIFE_EMAIL is not configured"""
        with patch.dict('os.environ', {}, clear=True):
            request = actions.ToggleIgnoredRequest(email_id=sample_ignored_email.id)
            
            with pytest.raises(Exception) as exc_info:
                actions.toggle_ignored_email(request, session)
            
            assert "WIFE_EMAIL not configured" in str(exc_info.value)
            
            # Verify email status was not changed
            email = session.get(ProcessedEmail, sample_ignored_email.id)
            assert email.status == "ignored"
            
            # Verify no rule was created
            rules = session.exec(select(ManualRule)).all()
            assert len(rules) == 0
    
    def test_toggle_ignored_email_invalid_sender(self, session: Session):
        """Test handling when sender has no valid email pattern"""
        # Create email with invalid sender
        email = ProcessedEmail(
            email_id="invalid@test.com",
            subject="Test Email",
            sender="InvalidSender",
            received_at=datetime.now(timezone.utc),
            processed_at=datetime.now(timezone.utc),
            status="ignored",
            account_email="user1@example.com",
            category=None,
            reason="Not a receipt",
        )
        session.add(email)
        session.commit()
        session.refresh(email)
        
        request = actions.ToggleIgnoredRequest(email_id=email.id)
        
        with pytest.raises(Exception) as exc_info:
            actions.toggle_ignored_email(request, session)
        
        assert "Could not extract email pattern" in str(exc_info.value)
