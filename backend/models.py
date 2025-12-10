from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class ProcessedEmail(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email_id: str = Field(index=True, unique=True)  # Message-ID header
    subject: str
    sender: str
    received_at: datetime
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    status: str  # "forwarded", "blocked", "error"
    account_email: Optional[str] = None  # The account that received this email
    category: Optional[str] = None  # "amazon", "receipt", "spam", etc.
    amount: Optional[float] = None
    reason: Optional[str] = None  # Why it was blocked or forwarded


class Stats(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: datetime = Field(default_factory=datetime.utcnow)
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
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ManualRule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email_pattern: Optional[str] = None  # Wildcard supported
    subject_pattern: Optional[str] = None  # Wildcard supported
    priority: int = 10
    purpose: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProcessingRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    emails_checked: int = 0  # Number of emails fetched
    emails_processed: int = 0  # Number of emails actually processed (new ones)
    emails_forwarded: int = 0  # Number of emails forwarded
    status: str = "completed"  # "running", "completed", "error"
    error_message: Optional[str] = None
    check_interval_minutes: Optional[int] = (
        None  # The configured interval at the time of run
    )
