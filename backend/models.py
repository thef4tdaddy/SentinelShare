from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


# Helper for aware UTC default
def utc_now():
    return datetime.now(timezone.utc)


class ProcessedEmail(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email_id: Optional[str] = Field(
        default=None, index=True, unique=True
    )  # Message-ID header
    content_hash: Optional[str] = Field(default=None, index=True)
    subject: Optional[str] = None
    sender: Optional[str] = None
    received_at: Optional[datetime] = None
    processed_at: Optional[datetime] = Field(default_factory=utc_now)
    status: Optional[str] = None  # "forwarded", "blocked", "error"
    account_email: Optional[str] = None  # The account that received this email
    category: Optional[str] = None  # "amazon", "receipt", "spam", etc.
    amount: Optional[float] = None
    reason: Optional[str] = None  # Why it was blocked or forwarded
    encrypted_body: Optional[str] = None
    encrypted_html: Optional[str] = None
    retention_expires_at: Optional[datetime] = None


class Stats(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: datetime = Field(default_factory=utc_now)
    forwarded_count: int = 0
    blocked_count: int = 0
    total_amount_processed: float = 0.0


class GlobalSettings(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True)
    value: str
    description: Optional[str] = None


class Preference(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    item: str  # e.g. "amazon", "restaurants"
    type: str  # "Blocked Sender", "Always Forward", "Blocked Category"
    created_at: datetime = Field(default_factory=utc_now)


class ManualRule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email_pattern: Optional[str] = None  # Wildcard supported
    subject_pattern: Optional[str] = None  # Wildcard supported
    priority: int = 10
    purpose: Optional[str] = None
    confidence: float = 1.0  # 0.0 to 1.0
    is_shadow_mode: bool = False  # If True, rule doesn't affect forwarding
    match_count: int = 0  # To track successful matches in shadow mode
    created_at: datetime = Field(default_factory=utc_now)


class ProcessingRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: Optional[datetime] = None
    emails_checked: int = 0  # Number of emails fetched
    emails_processed: int = 0  # Number of emails actually processed (new ones)
    emails_forwarded: int = 0  # Number of emails forwarded
    status: str = "completed"  # "running", "completed", "error"
    error_message: Optional[str] = None
    check_interval_minutes: Optional[int] = (
        None  # The configured interval at the time of run
    )


class LearningCandidate(SQLModel, table=True):
    """
    Represents a potential rule discovered by the Retroactive Learning scanner.
    Stores patterns, not email content, to respect privacy.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    sender: str
    subject_pattern: Optional[str] = None
    confidence: float
    type: str = "Receipt"
    matches: int = 1  # How many emails matched this pattern during scan
    example_subject: Optional[str] = None  # One example subject for context
    created_at: datetime = Field(default_factory=utc_now)


class EmailAccount(SQLModel, table=True):
    """
    Represents an email account for monitoring receipts.
    Passwords are encrypted at rest using the SECRET_KEY.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)  # Email address
    host: str = Field(default="imap.gmail.com")  # IMAP server host
    port: int = Field(default=993)  # IMAP server port
    username: str  # Username for IMAP login (usually same as email)
    encrypted_password: str  # Encrypted password using Fernet
    is_active: bool = Field(default=True)  # Whether to monitor this account
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), onupdate=utc_now),
    )
