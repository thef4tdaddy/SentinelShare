"""
Authentication utilities for user management.
Handles password hashing, verification, and user creation.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, Request
from sqlmodel import Session, select

from backend.database import get_session
from backend.models import User


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def create_user(
    session: Session,
    username: str,
    email: str,
    password: str,
    is_admin: bool = False,
    forwarding_target_email: Optional[str] = None,
) -> User:
    """
    Create a new user with hashed password.
    
    Args:
        session: Database session
        username: Unique username
        email: User email (must be unique)
        password: Plain text password (will be hashed)
        is_admin: Whether user has admin privileges
        forwarding_target_email: Email address to forward receipts to
    
    Returns:
        Created User object
    
    Raises:
        ValueError: If username or email already exists
    """
    # Check for existing username
    existing = session.exec(select(User).where(User.username == username)).first()
    if existing:
        raise ValueError(f"Username '{username}' already exists")
    
    # Check for existing email
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing:
        raise ValueError(f"Email '{email}' already exists")
    
    # Create user
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        is_admin=is_admin,
        is_active=True,
        forwarding_target_email=forwarding_target_email,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user


def authenticate_user(session: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate a user by username and password.
    
    Args:
        session: Database session
        username: Username to authenticate
        password: Plain text password
    
    Returns:
        User object if authentication succeeds, None otherwise
    """
    user = session.exec(select(User).where(User.username == username)).first()
    
    if not user:
        return None
    
    if not user.is_active:
        return None
    
    if not verify_password(password, user.password_hash):
        return None
    
    return user


def get_current_user(request: Request, session: Session = Depends(get_session)) -> User:
    """
    Dependency to get the current authenticated user from the request session.
    
    Args:
        request: FastAPI request object
        session: Database session
    
    Returns:
        Current authenticated User object
    
    Raises:
        HTTPException: If user is not authenticated or not found
    """
    user_id = request.session.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = session.get(User, user_id)
    
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    return user


def get_current_user_optional(
    request: Request, session: Session = Depends(get_session)
) -> Optional[User]:
    """
    Optional dependency to get the current authenticated user.
    Returns None if user is not authenticated instead of raising an exception.
    
    Args:
        request: FastAPI request object
        session: Database session
    
    Returns:
        Current authenticated User object or None
    """
    user_id = request.session.get("user_id")
    
    if not user_id:
        return None
    
    user = session.get(User, user_id)
    
    if not user or not user.is_active:
        return None
    
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to require admin privileges.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Current user if admin
    
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    return current_user


def get_or_create_legacy_user(session: Session) -> Optional[User]:
    """
    Get or create a legacy user for backward compatibility with single-user mode.
    This is used when DASHBOARD_PASSWORD is set but no users exist in the database.
    
    Args:
        session: Database session
    
    Returns:
        Legacy user or None if DASHBOARD_PASSWORD is not set
    """
    dashboard_password = os.environ.get("DASHBOARD_PASSWORD")
    
    if not dashboard_password:
        return None
    
    # Check if any users exist
    existing_user = session.exec(select(User)).first()
    
    if existing_user:
        # Users exist, don't create legacy user
        return None
    
    # Create a legacy admin user with DASHBOARD_PASSWORD
    legacy_email = os.environ.get("WIFE_EMAIL", "admin@localhost")
    
    try:
        user = create_user(
            session=session,
            username="admin",
            email=legacy_email,
            password=dashboard_password,
            is_admin=True,
            forwarding_target_email=legacy_email,
        )
        return user
    except ValueError:
        # User already exists
        return session.exec(select(User).where(User.username == "admin")).first()
