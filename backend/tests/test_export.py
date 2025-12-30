import csv
import io
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from backend.database import get_session
from backend.main import app
from backend.models import ProcessedEmail
from backend.routers.history import EmailStatus


@pytest.fixture(autouse=True)
def disable_auth(monkeypatch):
    """Disable dashboard authentication for all tests in this file"""
    monkeypatch.delenv("DASHBOARD_PASSWORD", raising=False)


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_export_no_filters(client, session: Session):
    # Add some test data
    email1 = ProcessedEmail(
        email_id="1",
        subject="Receipt 1",
        sender="vendor1@example.com",
        processed_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        received_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        status=EmailStatus.FORWARDED,
        amount=10.0,
        category="Food",
    )
    email2 = ProcessedEmail(
        email_id="2",
        subject="Notification 1",
        sender="info@example.com",
        processed_at=datetime(2025, 1, 2, tzinfo=timezone.utc),
        received_at=datetime(2025, 1, 2, tzinfo=timezone.utc),
        status=EmailStatus.IGNORED,
        amount=None,
        category=None,
    )
    session.add(email1)
    session.add(email2)
    session.commit()

    response = client.get("/api/history/export?format=csv")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert 'attachment; filename="expenses_' in response.headers["content-disposition"]

    # Read CSV
    content = response.text
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)

    assert len(rows) == 3  # Header + 2 data rows
    assert rows[0] == [
        "Date",
        "Vendor",
        "Amount",
        "Currency",
        "Category",
        "Link to Receipt",
    ]
    # email2 is processed later, so it appears first in desc order
    assert rows[1][1] == "info@example.com"
    assert rows[1][2] == ""
    assert rows[2][1] == "vendor1@example.com"
    assert rows[2][2] == "10.00"


def test_export_with_filters(client, session: Session):
    # Add test data
    email1 = ProcessedEmail(
        email_id="1",
        subject="Amazon Receipt",
        sender="no-reply@amazon.com",
        processed_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        received_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        status=EmailStatus.FORWARDED,
        amount=15.99,
        category="Shopping",
    )
    email2 = ProcessedEmail(
        email_id="2",
        subject="Uber Receipt",
        sender="uber@uber.com",
        processed_at=datetime(2025, 1, 5, tzinfo=timezone.utc),
        received_at=datetime(2025, 1, 5, tzinfo=timezone.utc),
        status=EmailStatus.FORWARDED,
        amount=25.0,
        category="Transport",
    )
    session.add(email1)
    session.add(email2)
    session.commit()

    # Filter by sender
    response = client.get("/api/history/export?format=csv&sender=amazon")
    assert response.status_code == 200
    reader = csv.reader(io.StringIO(response.text))
    rows = list(reader)
    assert len(rows) == 2  # Header + 1 row
    assert rows[1][1] == "no-reply@amazon.com"

    # Filter by date range
    response = client.get(
        "/api/history/export?format=csv&date_from=2025-01-02T00:00:00Z"
    )
    assert response.status_code == 200
    reader = csv.reader(io.StringIO(response.text))
    rows = list(reader)
    assert len(rows) == 2  # Header + 1 row (Uber)
    assert rows[1][1] == "uber@uber.com"

    # Filter by amount range
    response = client.get("/api/history/export?format=csv&min_amount=20")
    assert response.status_code == 200
    reader = csv.reader(io.StringIO(response.text))
    rows = list(reader)
    assert len(rows) == 2  # Header + 1 row (Uber)
    assert rows[1][2] == "25.00"


def test_csv_injection_sanitization(client, session: Session):
    # Add potentially dangerous data
    email = ProcessedEmail(
        email_id="1",
        subject="=SUM(A1:B2)",  # Dangerous subject but not exported as is
        sender="=dangerous@vendor.com",
        processed_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        status=EmailStatus.FORWARDED,
        category="+DangerousCategory",
    )
    session.add(email)
    session.commit()

    response = client.get("/api/history/export?format=csv")
    assert response.status_code == 200
    reader = csv.reader(io.StringIO(response.text))
    rows = list(reader)

    # Check that dangerous characters are prefixed with a single quote
    assert rows[1][1] == "'=dangerous@vender.com"
    assert rows[1][4] == "'+DangerousCategory"
