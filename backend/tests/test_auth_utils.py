"""
Tests for user authentication utilities.
"""

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from backend.auth_utils import (
    authenticate_user,
    create_user,
    hash_password,
    verify_password,
)
from backend.models import User


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


class TestPasswordHashing:
    """Tests for password hashing and verification"""

    def test_hash_password(self):
        """Test password hashing"""
        password = "test_password_123"
        hashed = hash_password(password)
        
        # Hash should be different from password
        assert hashed != password
        # Hash should be a string
        assert isinstance(hashed, str)
        # Hash should not be empty
        assert len(hashed) > 0

    def test_verify_password(self):
        """Test password verification"""
        password = "test_password_123"
        hashed = hash_password(password)
        
        # Correct password should verify
        assert verify_password(password, hashed) is True
        
        # Wrong password should not verify
        assert verify_password("wrong_password", hashed) is False

    def test_verify_password_with_invalid_hash(self):
        """Test password verification with invalid hash"""
        result = verify_password("password", "invalid_hash")
        assert result is False


class TestUserCreation:
    """Tests for user creation"""

    def test_create_user(self, session: Session):
        """Test creating a new user"""
        user = create_user(
            session=session,
            username="testuser",
            email="test@example.com",
            password="testpass123",
            is_admin=False,
            forwarding_target_email="forward@example.com",
        )
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_admin is False
        assert user.is_active is True
        assert user.forwarding_target_email == "forward@example.com"
        
        # Password should be hashed
        assert user.password_hash != "testpass123"
        assert verify_password("testpass123", user.password_hash)

    def test_create_admin_user(self, session: Session):
        """Test creating an admin user"""
        user = create_user(
            session=session,
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            is_admin=True,
        )
        
        assert user.is_admin is True

    def test_create_user_duplicate_username(self, session: Session):
        """Test creating user with duplicate username fails"""
        create_user(
            session=session,
            username="duplicate",
            email="user1@example.com",
            password="pass123",
        )
        
        with pytest.raises(ValueError, match="Username .* already exists"):
            create_user(
                session=session,
                username="duplicate",
                email="user2@example.com",
                password="pass456",
            )

    def test_create_user_duplicate_email(self, session: Session):
        """Test creating user with duplicate email fails"""
        create_user(
            session=session,
            username="user1",
            email="duplicate@example.com",
            password="pass123",
        )
        
        with pytest.raises(ValueError, match="Email .* already exists"):
            create_user(
                session=session,
                username="user2",
                email="duplicate@example.com",
                password="pass456",
            )


class TestUserAuthentication:
    """Tests for user authentication"""

    def test_authenticate_user_success(self, session: Session):
        """Test successful user authentication"""
        # Create a user
        create_user(
            session=session,
            username="authuser",
            email="auth@example.com",
            password="correctpass",
        )
        
        # Authenticate with correct credentials
        user = authenticate_user(session, "authuser", "correctpass")
        
        assert user is not None
        assert user.username == "authuser"
        assert user.email == "auth@example.com"

    def test_authenticate_user_wrong_password(self, session: Session):
        """Test authentication with wrong password"""
        create_user(
            session=session,
            username="authuser2",
            email="auth2@example.com",
            password="correctpass",
        )
        
        user = authenticate_user(session, "authuser2", "wrongpass")
        
        assert user is None

    def test_authenticate_user_nonexistent(self, session: Session):
        """Test authentication with non-existent user"""
        user = authenticate_user(session, "nonexistent", "password")
        
        assert user is None

    def test_authenticate_inactive_user(self, session: Session):
        """Test authentication with inactive user"""
        user = create_user(
            session=session,
            username="inactive",
            email="inactive@example.com",
            password="password",
        )
        
        # Deactivate the user
        user.is_active = False
        session.add(user)
        session.commit()
        
        # Try to authenticate
        result = authenticate_user(session, "inactive", "password")
        
        assert result is None
