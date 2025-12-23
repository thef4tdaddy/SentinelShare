from unittest.mock import Mock, patch

from backend.migration_utils import run_migrations


class TestMigrationUtils:
    """Tests for migration_utils.py to achieve full coverage"""

    def test_run_migrations_no_alembic_ini(self, tmp_path, monkeypatch, capsys):
        """Test that run_migrations returns early when alembic.ini is missing"""
        # Change to a directory without alembic.ini
        monkeypatch.chdir(tmp_path)

        run_migrations()

        captured = capsys.readouterr()
        assert "Warning: alembic.ini not found. Skipping migrations." in captured.out

    @patch("backend.migration_utils.os.path.exists")
    @patch("backend.migration_utils.Config")
    @patch("backend.migration_utils.inspect")
    @patch("backend.migration_utils.command")
    def test_run_migrations_with_alembic_ini_normal_flow(
        self, mock_command, mock_inspect, mock_config, mock_exists, capsys
    ):
        """Test normal migration flow when alembic.ini exists and no legacy tables"""
        # Mock that alembic.ini exists
        mock_exists.return_value = True

        # Mock Config to return a config object
        mock_alembic_cfg = Mock()
        mock_config.return_value = mock_alembic_cfg

        # Mock inspector to return tables with alembic_version present
        mock_inspector = Mock()
        mock_inspector.get_table_names.return_value = [
            "processedemail",
            "alembic_version",
            "stats",
        ]
        mock_inspect.return_value = mock_inspector

        run_migrations()

        captured = capsys.readouterr()

        # Verify Config was called with alembic.ini path (line 23)
        mock_config.assert_called_once_with("alembic.ini")

        # Verify inspector was created and get_table_names was called (lines 29-31)
        mock_inspect.assert_called_once()
        mock_inspector.get_table_names.assert_called_once()

        # Verify upgrade was called but stamp was NOT called (normal flow)
        mock_command.upgrade.assert_called_once_with(mock_alembic_cfg, "head")
        mock_command.stamp.assert_not_called()

        # Verify output messages (lines 44-46)
        assert "Applying pending migrations..." in captured.out
        assert "Migrations complete." in captured.out

    @patch("backend.migration_utils.os.path.exists")
    @patch("backend.migration_utils.Config")
    @patch("backend.migration_utils.inspect")
    @patch("backend.migration_utils.command")
    def test_run_migrations_legacy_database_detection(
        self, mock_command, mock_inspect, mock_config, mock_exists, capsys
    ):
        """Test legacy database detection and stamping when alembic_version is missing"""
        # Mock that alembic.ini exists
        mock_exists.return_value = True

        # Mock Config to return a config object
        mock_alembic_cfg = Mock()
        mock_config.return_value = mock_alembic_cfg

        # Mock inspector to return tables WITHOUT alembic_version (legacy state)
        mock_inspector = Mock()
        mock_inspector.get_table_names.return_value = [
            "processedemail",
            "stats",
            "globalsettings",
        ]
        mock_inspect.return_value = mock_inspector

        run_migrations()

        captured = capsys.readouterr()

        # Verify Config was called (line 23)
        mock_config.assert_called_once_with("alembic.ini")

        # Verify inspector was created (lines 29-31)
        mock_inspect.assert_called_once()
        mock_inspector.get_table_names.assert_called_once()

        # Verify stamp was called for legacy database (lines 34-41)
        mock_command.stamp.assert_called_once_with(mock_alembic_cfg, "head")
        assert "Detected existing tables without Alembic history" in captured.out

        # Verify upgrade was also called after stamping
        mock_command.upgrade.assert_called_once_with(mock_alembic_cfg, "head")

        # Verify completion message
        assert "Migrations complete." in captured.out

    @patch("backend.migration_utils.os.path.exists")
    @patch("backend.migration_utils.Config")
    @patch("backend.migration_utils.inspect")
    def test_run_migrations_exception_handling(
        self, mock_inspect, mock_config, mock_exists, capsys
    ):
        """Test exception handling during migrations"""
        # Mock that alembic.ini exists
        mock_exists.return_value = True

        # Mock Config to return a config object
        mock_alembic_cfg = Mock()
        mock_config.return_value = mock_alembic_cfg

        # Mock inspector to raise an exception
        mock_inspect.side_effect = Exception("Database connection error")

        # Should not raise, just log the error
        run_migrations()

        captured = capsys.readouterr()

        # Verify Config was called (line 23)
        mock_config.assert_called_once_with("alembic.ini")

        # Verify error message is printed (lines 48-49)
        assert "Error running migrations:" in captured.out
        assert "Database connection error" in captured.out

    @patch("backend.migration_utils.os.path.exists")
    @patch("backend.migration_utils.Config")
    @patch("backend.migration_utils.inspect")
    @patch("backend.migration_utils.command")
    def test_run_migrations_no_legacy_tables(
        self, mock_command, mock_inspect, mock_config, mock_exists
    ):
        """Test when there are no processedemail tables (new database)"""
        # Mock that alembic.ini exists
        mock_exists.return_value = True

        # Mock Config to return a config object
        mock_alembic_cfg = Mock()
        mock_config.return_value = mock_alembic_cfg

        # Mock inspector to return no app tables
        mock_inspector = Mock()
        mock_inspector.get_table_names.return_value = []
        mock_inspect.return_value = mock_inspector

        run_migrations()

        # Verify stamp was NOT called (no legacy tables)
        mock_command.stamp.assert_not_called()

        # Verify upgrade was still called
        mock_command.upgrade.assert_called_once_with(mock_alembic_cfg, "head")

    @patch("backend.migration_utils.os.path.exists")
    @patch("backend.migration_utils.Config")
    @patch("backend.migration_utils.inspect")
    @patch("backend.migration_utils.command")
    def test_run_migrations_with_alembic_version_present(
        self, mock_command, mock_inspect, mock_config, mock_exists
    ):
        """Test when alembic_version exists but processedemail doesn't"""
        # Mock that alembic.ini exists
        mock_exists.return_value = True

        # Mock Config to return a config object
        mock_alembic_cfg = Mock()
        mock_config.return_value = mock_alembic_cfg

        # Mock inspector to return alembic_version but no processedemail
        mock_inspector = Mock()
        mock_inspector.get_table_names.return_value = ["alembic_version"]
        mock_inspect.return_value = mock_inspector

        run_migrations()

        # Verify stamp was NOT called (alembic_version exists)
        mock_command.stamp.assert_not_called()

        # Verify upgrade was called
        mock_command.upgrade.assert_called_once_with(mock_alembic_cfg, "head")
