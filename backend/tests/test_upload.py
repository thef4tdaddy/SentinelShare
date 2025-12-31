import io
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from backend.main import app
from backend.models import ProcessedEmail

MOCK_SECRET = "cpUbNMiXWufM3gAPx1arHE1h7Y72s9sBri-MDiWtwb4="
MOCK_PASSWORD = "mock-password-for-testing"


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


@pytest.fixture(name="client")
def client_fixture(session):
    """Create a test client with mocked dependencies"""

    def get_session_override():
        return session

    from backend.database import get_session

    app.dependency_overrides[get_session] = get_session_override

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@patch.dict(os.environ, {"SECRET_KEY": MOCK_SECRET, "DASHBOARD_PASSWORD": ""})
def test_upload_receipt_pdf(client, session):
    """Test uploading a PDF receipt"""
    # Create a mock PDF file
    pdf_content = b"%PDF-1.4\n%test content"
    files = {"file": ("test_receipt.pdf", io.BytesIO(pdf_content), "application/pdf")}

    response = client.post("/api/actions/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "test_receipt.pdf" in data["message"]
    assert "file_path" in data
    assert "record_id" in data

    # Verify database record
    record = session.get(ProcessedEmail, data["record_id"])
    assert record is not None
    assert record.status == "manual_upload"
    assert record.sender == "manual_upload"
    assert "test_receipt.pdf" in record.subject

    # Cleanup
    if os.path.exists(data["file_path"]):
        os.remove(data["file_path"])


@patch.dict(os.environ, {"SECRET_KEY": MOCK_SECRET, "DASHBOARD_PASSWORD": ""})
def test_upload_receipt_image(client, session):
    """Test uploading an image receipt"""
    # Create a mock PNG file (minimal valid PNG header)
    png_header = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    files = {"file": ("receipt.png", io.BytesIO(png_header), "image/png")}

    response = client.post("/api/actions/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # Cleanup
    if os.path.exists(data["file_path"]):
        os.remove(data["file_path"])


@patch.dict(os.environ, {"SECRET_KEY": MOCK_SECRET, "DASHBOARD_PASSWORD": ""})
def test_upload_receipt_invalid_type(client):
    """Test uploading an invalid file type"""
    files = {"file": ("test.txt", io.BytesIO(b"test content"), "text/plain")}

    response = client.post("/api/actions/upload", files=files)

    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


@patch.dict(os.environ, {"SECRET_KEY": MOCK_SECRET, "DASHBOARD_PASSWORD": ""})
def test_upload_receipt_too_large(client):
    """Test uploading a file that's too large"""
    # Create a file larger than 10MB
    large_content = b"x" * (11 * 1024 * 1024)  # 11MB
    files = {"file": ("large.pdf", io.BytesIO(large_content), "application/pdf")}

    response = client.post("/api/actions/upload", files=files)

    assert response.status_code == 400
    assert "exceeds 10MB limit" in response.json()["detail"]


@patch.dict(os.environ, {"SECRET_KEY": MOCK_SECRET, "DASHBOARD_PASSWORD": "test123"})
def test_upload_receipt_requires_auth(client):
    """Test that upload requires authentication when password is set"""
    pdf_content = b"%PDF-1.4\n%test"
    files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}

    response = client.post("/api/actions/upload", files=files)

    assert response.status_code == 401


@patch.dict(os.environ, {"SECRET_KEY": MOCK_SECRET, "DASHBOARD_PASSWORD": ""})
def test_upload_receipt_file_write_error(client, session):
    """Test handling of file write errors during upload"""
    pdf_content = b"%PDF-1.4\n%test content"
    files = {"file": ("test_receipt.pdf", io.BytesIO(pdf_content), "application/pdf")}

    # Mock the open() builtin to raise an error during file write
    with patch("builtins.open", side_effect=PermissionError("Permission denied")):
        response = client.post("/api/actions/upload", files=files)

        assert response.status_code == 500
        assert "Failed to save file" in response.json()["detail"]
        assert "Permission denied" in response.json()["detail"]


@patch.dict(os.environ, {"SECRET_KEY": MOCK_SECRET, "DASHBOARD_PASSWORD": ""})
def test_upload_receipt_database_error_with_cleanup(client, session, tmp_path):
    """Test handling of database errors with file cleanup during upload"""
    pdf_content = b"%PDF-1.4\n%test content"
    files = {"file": ("test_receipt.pdf", io.BytesIO(pdf_content), "application/pdf")}

    # Track files that were created
    created_files = []
    removed_files = []
    original_open = open
    original_remove = os.remove

    def tracking_open(file, *args, **kwargs):
        """Track file creation and redirect to tmp_path for isolation"""
        mode = args[0] if args else kwargs.get("mode", "r")

        # For write modes, track the file
        if isinstance(file, str) and any(char in mode for char in ("w", "a", "x")):
            created_files.append(file)

        return original_open(file, *args, **kwargs)

    def tracking_remove(path):
        """Track file removal"""
        removed_files.append(path)
        # Actually remove the file if it exists
        if os.path.exists(path):
            return original_remove(path)

    with patch("builtins.open", side_effect=tracking_open):
        with patch("os.remove", side_effect=tracking_remove):
            # Mock session.commit to raise an error
            with patch.object(
                session, "commit", side_effect=Exception("Database error")
            ):
                response = client.post("/api/actions/upload", files=files)

                assert response.status_code == 500
                assert "Failed to create database record" in response.json()["detail"]
                assert "Database error" in response.json()["detail"]

                # Verify that file was created and then cleaned up after error
                assert len(created_files) > 0, "Expected file to be created"
                assert len(removed_files) > 0, "Expected file to be cleaned up"
                assert (
                    created_files[0] == removed_files[0]
                ), "Expected cleanup to remove the created file"
