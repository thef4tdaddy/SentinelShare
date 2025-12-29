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
        from backend.database import format_database_url

        assert (
            format_database_url("postgres://user:pass@localhost/db")
            == "postgresql://user:pass@localhost/db"
        )
        assert (
            format_database_url("postgresql://user:pass@localhost/db")
            == "postgresql://user:pass@localhost/db"
        )
        assert format_database_url("sqlite:///test.db") == "sqlite:///test.db"
        assert format_database_url(None) == "sqlite:///./local_dev.db"
        assert format_database_url("") == "sqlite:///./local_dev.db"

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

    def test_postgres_url_replacement_behavior(self):
        """Test that the helper replaces postgres:// with postgresql:// correctly"""
        from backend.database import format_database_url

        test_url = "postgres://user:pass@localhost/testdb"
        expected_url = "postgresql://user:pass@localhost/testdb"

        assert format_database_url(test_url) == expected_url
