import os
from unittest.mock import patch

from backend.database import create_db_and_tables, get_session
from sqlmodel import Session, SQLModel


class TestDatabase:

    def test_get_session_yields_session(self):
        """Test that get_session yields a valid Session"""
        session_generator = get_session()
        session = next(session_generator)

        assert isinstance(session, Session)

        # Clean up
        try:
            next(session_generator)
        except StopIteration:
            pass

    def test_create_db_and_tables(self):
        """Test that create_db_and_tables creates tables without errors"""
        # This should not raise any exceptions
        create_db_and_tables()

        # Verify tables were created by checking metadata
        assert len(SQLModel.metadata.tables) > 0

        # Check that expected tables exist
        table_names = [table.name for table in SQLModel.metadata.tables.values()]
        assert "processedemail" in table_names
        assert "stats" in table_names
        assert "globalsettings" in table_names
        assert "preference" in table_names
        assert "manualrule" in table_names

    @patch.dict(os.environ, {"DATABASE_URL": "postgres://user:pass@localhost/db"})
    def test_database_url_postgres_replacement(self):
        """Test that postgres:// URLs are replaced with postgresql://"""
        # Import fresh to get the patched env var
        import importlib

        from backend import database

        importlib.reload(database)

        # The module should have replaced postgres:// with postgresql://
        assert database.database_url.startswith("postgresql://")

    @patch.dict(os.environ, {"DATABASE_URL": "postgresql://user:pass@localhost/db"})
    def test_database_url_postgresql_unchanged(self):
        """Test that postgresql:// URLs remain unchanged"""
        import importlib

        from backend import database

        importlib.reload(database)

        assert database.database_url == "postgresql://user:pass@localhost/db"

    @patch.dict(os.environ, {}, clear=True)
    def test_database_url_fallback_to_sqlite(self):
        """Test that database falls back to SQLite when DATABASE_URL not set"""
        import importlib

        from backend import database

        importlib.reload(database)

        assert "sqlite" in database.database_url
        assert "local_dev.db" in database.database_url

    def test_engine_exists(self):
        """Test that engine is created"""
        from backend.database import engine

        assert engine is not None

    def test_session_context_manager(self):
        """Test that session can be used as context manager"""
        session_gen = get_session()
        session = next(session_gen)

        # Should be able to use session
        assert session is not None

        # Close properly
        try:
            next(session_gen)
        except StopIteration:
            pass
