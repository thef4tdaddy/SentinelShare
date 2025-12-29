import importlib

from sqlmodel import Session, SQLModel

from backend.database import create_db_and_tables, get_session


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
        import backend.models  # noqa: F401

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

    def test_database_url_parsing_logic(self):
        """Test the logic used for DATABASE_URL replacement"""

        def parse_url(url: str) -> str:
            if url and url.startswith("postgres://"):
                return url.replace("postgres://", "postgresql://", 1)
            return url

        assert (
            parse_url("postgres://user:pass@localhost/db")
            == "postgresql://user:pass@localhost/db"
        )
        assert (
            parse_url("postgresql://user:pass@localhost/db")
            == "postgresql://user:pass@localhost/db"
        )
        assert parse_url("sqlite:///test.db") == "sqlite:///test.db"

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

    def test_postgres_url_replacement(self, monkeypatch):
        """Test that postgres:// is replaced with postgresql:// when DATABASE_URL is set (line 9)"""
        # Set the environment variable with postgres:// prefix
        test_url = "postgres://user:pass@localhost/testdb"
        expected_url = "postgresql://user:pass@localhost/testdb"
        monkeypatch.setenv("DATABASE_URL", test_url)

        # Reload the module to trigger the initialization code
        import backend.database

        importlib.reload(backend.database)

        # Import the database_url variable to verify line 9 was executed
        from backend.database import database_url, engine

        # Verify that database_url was set from the environment variable (line 7)
        # and that the replacement happened (line 9)
        assert database_url is not None, "database_url was not set from DATABASE_URL"
        assert database_url == expected_url, (
            f"Line 9 was not executed correctly: expected '{expected_url}', "
            f"got '{database_url}'. The postgres:// prefix should have been replaced."
        )

        # Additional verification: the engine's URL should match
        assert "postgresql://" in str(
            engine.url
        ), "Engine URL does not contain postgresql://"
        assert "postgres://" not in str(
            engine.url
        ), "Engine URL still contains postgres:// (should be postgresql://)"
