from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from backend.models import ManualRule, ProcessedEmail
from backend.routers import actions
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool


@pytest.fixture(name="engine")
def engine_fixture():
    """Create an in-memory database engine for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="session")
def session_fixture(engine):
    """Create an in-memory database session for testing"""
    with Session(engine) as session:
        yield session


@pytest.fixture(name="sample_ignored_email")
def sample_ignored_email_fixture(session):
    """Create a sample ignored email for testing"""
    now = datetime.now(timezone.utc)
    # ...

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

    def test_toggle_ignored_email_success(self, session, sample_ignored_email):
        """Test successfully toggling an ignored email"""
        # Mock the EmailForwarder and environment
        with patch.dict("os.environ", {"WIFE_EMAIL": "wife@example.com"}):
            with patch(
                "backend.routers.actions.EmailForwarder.forward_email",
                return_value=True,
            ):
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

        with patch.dict("os.environ", {"WIFE_EMAIL": "wife@example.com"}):
            with patch(
                "backend.routers.actions.EmailForwarder.forward_email",
                return_value=True,
            ):
                assert email.id is not None
                request = actions.ToggleIgnoredRequest(email_id=email.id)
                result = actions.toggle_ignored_email(request, session)

                assert result["success"] is True

                # Check that rule was created with extracted email
                rules = session.exec(select(ManualRule)).all()
                assert len(rules) == 1
                assert rules[0].email_pattern == "john@example.com"

    def test_toggle_ignored_email_not_found(self, session):
        """Test toggling a non-existent email"""
        request = actions.ToggleIgnoredRequest(email_id=9999)

        with pytest.raises(Exception) as exc_info:
            actions.toggle_ignored_email(request, session)

        assert "not found" in str(exc_info.value).lower()

    def test_toggle_non_ignored_email(self, session):
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

    def test_toggle_ignored_email_forward_failure(self, session, sample_ignored_email):
        """Test handling when email forwarding fails"""
        with patch.dict("os.environ", {"WIFE_EMAIL": "wife@example.com"}):
            with patch(
                "backend.routers.actions.EmailForwarder.forward_email",
                return_value=False,
            ):
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

    def test_toggle_ignored_email_missing_wife_email(
        self, session, sample_ignored_email
    ):
        """Test handling when WIFE_EMAIL is not configured"""
        with patch.dict("os.environ", {}, clear=True):
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

    def test_toggle_ignored_email_invalid_sender(self, session):
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

    def test_toggle_ignored_email_existing_rule(self, session):
        """Test toggling ignored email when manual rule already exists"""
        # Create an existing manual rule
        existing_rule = ManualRule(
            email_pattern="existing@company.com",
            subject_pattern=None,
            priority=100,
            purpose="Pre-existing rule",
        )
        session.add(existing_rule)
        session.commit()

        # Create an ignored email with matching sender
        email = ProcessedEmail(
            email_id="existing-email@test.com",
            subject="Newsletter from Company",
            sender="existing@company.com",
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

        with patch.dict("os.environ", {"WIFE_EMAIL": "wife@example.com"}):
            with patch(
                "backend.routers.actions.EmailForwarder.forward_email",
                return_value=True,
            ):
                request = actions.ToggleIgnoredRequest(email_id=email.id)
                result = actions.toggle_ignored_email(request, session)

                assert result["success"] is True
                # Verify no new rule was created (should reuse existing)
                rules = session.exec(
                    select(ManualRule).where(
                        ManualRule.email_pattern == "existing@company.com"
                    )
                ).all()
                assert len(rules) == 1
                assert rules[0].purpose == "Pre-existing rule"


class TestAccountSelection:
    """Tests for account credential extraction and fallback in toggle_ignored_email"""

    def test_account_selection_from_accounts_json(self, session, sample_ignored_email):
        import json

        accounts_json = json.dumps(
            [
                {
                    "email": "user1@example.com",
                    "password": "user1pass",
                    "imap_server": "imap.test.com",
                }
            ]
        )

        with patch.dict(
            "os.environ",
            {"WIFE_EMAIL": "wife@example.com", "EMAIL_ACCOUNTS": accounts_json},
        ):
            with patch(
                "backend.services.email_service.EmailService.fetch_email_by_id"
            ) as mock_fetch:
                mock_fetch.return_value = {
                    "body": "original content",
                    "html_body": "html content",
                }
                with patch(
                    "backend.routers.actions.EmailForwarder.forward_email",
                    return_value=True,
                ):
                    request = actions.ToggleIgnoredRequest(
                        email_id=sample_ignored_email.id
                    )
                    actions.toggle_ignored_email(request, session)

                    mock_fetch.assert_called_once_with(
                        "user1@example.com",
                        "user1pass",
                        sample_ignored_email.email_id,
                        "imap.test.com",
                    )

    def test_account_selection_fallback_to_all_accounts(
        self, session, sample_ignored_email
    ):
        import json

        accounts_json = json.dumps(
            [
                {"email": "primary@test.com", "password": "p1"},
                {"email": "fallback@test.com", "password": "f1"},
            ]
        )

        with patch.dict(
            "os.environ",
            {
                "WIFE_EMAIL": "wife@example.com",
                "EMAIL_ACCOUNTS": accounts_json,
                "SENDER_EMAIL": "none@test.com",  # Force not found
            },
        ):
            # Set sample_ignored_email.account_email to something not in the list
            sample_ignored_email.account_email = "missing@test.com"
            session.add(sample_ignored_email)
            session.commit()

            with patch(
                "backend.services.email_service.EmailService.fetch_email_by_id"
            ) as mock_fetch:
                # First attempt fails, second succeeds
                mock_fetch.side_effect = [None, {"body": "found"}]
                with patch(
                    "backend.routers.actions.EmailForwarder.forward_email",
                    return_value=True,
                ):
                    request = actions.ToggleIgnoredRequest(
                        email_id=sample_ignored_email.id
                    )
                    actions.toggle_ignored_email(request, session)

                    # Should try all accounts in EMAIL_ACCOUNTS
                    assert mock_fetch.call_count >= 2

    def test_account_selection_legacy_icloud(self, session, sample_ignored_email):
        with patch.dict(
            "os.environ",
            {
                "WIFE_EMAIL": "wife@example.com",
                "ICLOUD_EMAIL": "user1@example.com",
                "ICLOUD_PASSWORD": "icloudpass",
            },
        ):
            sample_ignored_email.account_email = "user1@example.com"
            session.add(sample_ignored_email)
            session.commit()

            with patch(
                "backend.services.email_service.EmailService.fetch_email_by_id"
            ) as mock_fetch:
                mock_fetch.return_value = {"body": "content"}
                with patch(
                    "backend.routers.actions.EmailForwarder.forward_email",
                    return_value=True,
                ):
                    request = actions.ToggleIgnoredRequest(
                        email_id=sample_ignored_email.id
                    )
                    actions.toggle_ignored_email(request, session)
                    mock_fetch.assert_called_once_with(
                        "user1@example.com",
                        "icloudpass",
                        sample_ignored_email.email_id,
                        "imap.mail.me.com",
                    )

    def test_account_selection_fallback_skips_already_tried(
        self, session, sample_ignored_email
    ):
        """Test that fallback logic skips the account that was already tried"""
        import json

        accounts_json = json.dumps(
            [
                {
                    "email": "sender@test.com",
                    "password": "p1",
                    "imap_server": "imap.test.com",
                },
                {"email": "fallback@test.com", "password": "f1"},
            ]
        )

        with patch.dict(
            "os.environ",
            {
                "WIFE_EMAIL": "wife@example.com",
                "EMAIL_ACCOUNTS": accounts_json,
                "SENDER_EMAIL": "sender@test.com",
                "SENDER_PASSWORD": "p1",
            },
        ):
            # Set sample_ignored_email.account_email to match SENDER_EMAIL
            sample_ignored_email.account_email = "sender@test.com"
            session.add(sample_ignored_email)
            session.commit()

            with patch(
                "backend.services.email_service.EmailService.fetch_email_by_id"
            ) as mock_fetch:
                # First attempt (sender@test.com) fails, fallback succeeds
                mock_fetch.side_effect = [None, {"body": "found"}]
                with patch(
                    "backend.routers.actions.EmailForwarder.forward_email",
                    return_value=True,
                ):
                    request = actions.ToggleIgnoredRequest(
                        email_id=sample_ignored_email.id
                    )
                    actions.toggle_ignored_email(request, session)

                    # Should call twice: once for initial, once for fallback
                    # But should skip sender@test.com in the loop since it was already tried
                    assert mock_fetch.call_count == 2
                    # Second call should be for fallback@test.com
                    calls = mock_fetch.call_args_list
                    assert calls[1][0][0] == "fallback@test.com"

    def test_account_selection_fallback_exception_handling(
        self, session, sample_ignored_email
    ):
        """Test that fallback handles JSON parsing errors gracefully"""
        with patch.dict(
            "os.environ",
            {
                "WIFE_EMAIL": "wife@example.com",
                "EMAIL_ACCOUNTS": "invalid-json{[",
                "SENDER_EMAIL": "test@test.com",
                "SENDER_PASSWORD": "pass",
            },
        ):
            sample_ignored_email.account_email = "test@test.com"
            session.add(sample_ignored_email)
            session.commit()

            with patch(
                "backend.services.email_service.EmailService.fetch_email_by_id"
            ) as mock_fetch:
                mock_fetch.return_value = None  # First attempt fails
                with patch(
                    "backend.routers.actions.EmailForwarder.forward_email",
                    return_value=True,
                ):
                    request = actions.ToggleIgnoredRequest(
                        email_id=sample_ignored_email.id
                    )
                    # Should not raise exception, should continue with placeholder body
                    result = actions.toggle_ignored_email(request, session)
                    assert result["success"] is True
                    # Should only call fetch once (initial attempt)
                    assert mock_fetch.call_count == 1


class TestQuickAction:
    """Tests for the quick action endpoint"""

    def test_quick_stop_success(self, monkeypatch):
        import hashlib
        import hmac
        import time

        secret = "test-secret"
        monkeypatch.setenv("SECRET_KEY", secret)
        from backend.routers import actions

        actions.SECRET = secret  # Force refresh

        ts = str(time.time())
        cmd = "STOP"
        arg = "amazon.com"
        msg = f"{cmd}:{arg}:{ts}"
        sig = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()

        with patch(
            "backend.services.command_service.CommandService._add_preference"
        ) as mock_add:
            response = actions.quick_action(cmd, arg, ts, sig)
            assert "Successfully Blocked" in response
            mock_add.assert_called_once_with(arg, "Blocked Sender")

    def test_quick_more_success(self, monkeypatch):
        import hashlib
        import hmac
        import time

        secret = "test-secret"
        monkeypatch.setenv("SECRET_KEY", secret)
        from backend.routers import actions

        actions.SECRET = secret

        ts = str(time.time())
        cmd = "MORE"
        arg = "uber.com"
        msg = f"{cmd}:{arg}:{ts}"
        sig = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()

        with patch(
            "backend.services.command_service.CommandService._add_preference"
        ) as mock_add:
            response = actions.quick_action(cmd, arg, ts, sig)
            assert "Always Forwarding" in response
            mock_add.assert_called_once_with(arg, "Always Forward")

    def test_quick_settings_success(self, monkeypatch, session, engine):
        import hashlib
        import hmac
        import time

        from backend.models import Preference

        # Add some prefs to DB
        session.add(Preference(item="amazon", type="Blocked Category"))
        session.add(Preference(item="uber", type="Always Forward"))
        session.commit()

        secret = "test-secret"
        monkeypatch.setenv("SECRET_KEY", secret)
        from backend.routers import actions

        actions.SECRET = secret

        ts = str(time.time())
        cmd = "SETTINGS"
        arg = "none"
        msg = f"{cmd}:{arg}:{ts}"
        sig = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()

        with patch("backend.routers.actions.engine", engine):
            response = actions.quick_action(cmd, arg, ts, sig)
            assert "Current Settings" in response
            assert "amazon" in response
            assert "uber" in response

    def test_quick_block_category_success(self, monkeypatch):
        import hashlib
        import hmac
        import time

        secret = "test-secret"
        monkeypatch.setenv("SECRET_KEY", secret)
        from backend.routers import actions

        actions.SECRET = secret

        ts = str(time.time())
        cmd = "BLOCK_CATEGORY"
        arg = "Shopping"
        msg = f"{cmd}:{arg}:{ts}"
        sig = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()

        with patch(
            "backend.services.command_service.CommandService._add_preference"
        ) as mock_add:
            response = actions.quick_action(cmd, arg, ts, sig)
            assert "Blocked Category" in response
            mock_add.assert_called_once_with(arg, "Blocked Category")

    def test_quick_action_invalid_sig(self):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            actions.quick_action("STOP", "arg", "ts", "invalid-sig")
        assert exc.value.status_code == 403

    def test_quick_action_expired(self, monkeypatch):
        import hashlib
        import hmac
        import time

        secret = "test-secret"
        monkeypatch.setenv("SECRET_KEY", secret)
        from backend.routers import actions

        actions.SECRET = secret

        # 10 days ago
        ts = str(time.time() - 10 * 24 * 3600)
        cmd = "STOP"
        arg = "amazon.com"
        msg = f"{cmd}:{arg}:{ts}"
        sig = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()

        response = actions.quick_action(cmd, arg, ts, sig)
        assert "Link Expired" in response

    def test_quick_action_invalid_timestamp(self, monkeypatch):
        """Test handling of invalid timestamp format"""
        import hashlib
        import hmac

        secret = "test-secret"
        monkeypatch.setenv("SECRET_KEY", secret)
        from backend.routers import actions

        actions.SECRET = secret

        ts = "invalid-timestamp"
        cmd = "STOP"
        arg = "amazon.com"
        msg = f"{cmd}:{arg}:{ts}"
        sig = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()

        response = actions.quick_action(cmd, arg, ts, sig)
        assert "Invalid Timestamp" in response

    def test_quick_settings_empty(self, monkeypatch, session, engine):
        """Test SETTINGS command with no preferences"""
        import hashlib
        import hmac
        import time

        secret = "test-secret"
        monkeypatch.setenv("SECRET_KEY", secret)
        from backend.routers import actions

        actions.SECRET = secret

        ts = str(time.time())
        cmd = "SETTINGS"
        arg = "none"
        msg = f"{cmd}:{arg}:{ts}"
        sig = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()

        with patch("backend.routers.actions.engine", engine):
            response = actions.quick_action(cmd, arg, ts, sig)
            assert "No active preferences found yet" in response

    def test_quick_action_unknown_command(self, monkeypatch):
        """Test handling of unknown command"""
        import hashlib
        import hmac
        import time

        secret = "test-secret"
        monkeypatch.setenv("SECRET_KEY", secret)
        from backend.routers import actions

        actions.SECRET = secret

        ts = str(time.time())
        cmd = "UNKNOWN_CMD"
        arg = "test"
        msg = f"{cmd}:{arg}:{ts}"
        sig = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()

        response = actions.quick_action(cmd, arg, ts, sig)
        assert "Unknown Command" in response
