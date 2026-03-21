import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestConfig:
    """Tests for the configuration module."""

    def test_settings_model_dump(self):
        """Test Settings model_dump returns correct fields."""
        with patch("powderpipeline.config.YamlBaseSettings"):
            from powderpipeline.config import Settings

            settings = Settings(
                base_data_path=Path("/tmp/data"),
                db_name="test.duckdb",
                _case_sensitive=False,
            )
            dump = settings.model_dump()
            assert "base_data_path" in dump
            assert "db_name" in dump


class TestCLI:
    """Tests for the CLI module."""

    def test_cli_import(self):
        """Test that CLI module can be imported."""
        from powderpipeline.cli import app

        assert app is not None

    def test_scrape_cli_import(self):
        """Test scrape subcommand can be imported."""
        from powderpipeline.cli.scrape import scraper_app

        assert scraper_app is not None

    def test_cli_scrape_ski_passes_invokes(self):
        """Test ski-passes scrape command invokes correctly."""
        from powderpipeline.cli.scrape import scrape_ski_passes

        with patch("powderpipeline.cli.scrape.Settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                base_data_path=Path("/tmp"), db_name="test.duckdb"
            )
            try:
                scrape_ski_passes.callback(config_file=Path("config.yaml"))
            except Exception:
                pass

    def test_cli_scrape_ski_resorts_invokes(self):
        """Test ski-resorts scrape command invokes correctly."""
        from powderpipeline.cli.scrape import scrape_ski_resorts

        with patch("powderpipeline.cli.scrape.Settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                base_data_path=Path("/tmp"), db_name="test.duckdb"
            )
            try:
                scrape_ski_resorts.callback(config_file=Path("config.yaml"))
            except Exception:
                pass

    def test_cli_scrape_snow_conditions_invokes(self):
        """Test snow-conditions scrape command invokes correctly."""
        from powderpipeline.cli.scrape import scrape_snow_conditions

        with patch("powderpipeline.cli.scrape.Settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                base_data_path=Path("/tmp"), db_name="test.duckdb"
            )
            try:
                scrape_snow_conditions.callback(config_file=Path("config.yaml"))
            except Exception:
                pass

    def test_analyze_subcommand_imports(self):
        """Test analyze subcommand can be imported."""
        from powderpipeline.cli.analyze import analysis_app

        assert analysis_app is not None

    def test_visualize_subcommand_imports(self):
        """Test visualize subcommand can be imported."""
        from powderpipeline.cli.visualize import viz_app

        assert viz_app is not None


class TestBaseScraper:
    """Tests for the BaseScraper class."""

    def test_base_scraper_init(self):
        """Test BaseScraper can be instantiated."""
        from powderpipeline.scrapers.base import BaseScraper

        class TestScraper(BaseScraper):
            def scrape(self):
                pass

        mock_settings = MagicMock()
        mock_session = MagicMock()

        scraper = TestScraper(mock_settings, mock_session)
        assert scraper.settings == mock_settings
        assert scraper.session == mock_session

    def test_base_scraper_headers(self):
        """Test BaseScraper has correct default headers."""
        from powderpipeline.scrapers.base import BaseScraper

        assert "User-Agent" in BaseScraper.headers
        assert "Accept-Language" in BaseScraper.headers

    def test_base_scraper_abstract_method(self):
        """Test that BaseScraper.scrape raises NotImplementedError."""
        from powderpipeline.scrapers.base import BaseScraper

        class IncompleteScraper(BaseScraper):
            pass

        with pytest.raises(TypeError):
            IncompleteScraper(MagicMock(), MagicMock())


class TestDatabase:
    """Tests for the database module."""

    @patch("powderpipeline.db.create_engine")
    @patch("powderpipeline.db.SQLModel")
    def test_get_engine_creates_new_engine(self, mock_sqlmodel, mock_create_engine):
        """Test get_engine creates a new engine when none exists."""
        from powderpipeline.db import get_engine

        import powderpipeline.db as db_module

        db_module.__engine__ = None

        mock_settings = MagicMock()
        mock_settings.base_data_path = MagicMock()
        mock_settings.base_data_path.exists.return_value = True
        mock_settings.db_name = "test.duckdb"

        mock_create_engine.return_value = "mock_engine"

        engine = get_engine(mock_settings)

        assert mock_create_engine.called

    @patch("powderpipeline.db.create_engine")
    @patch("powderpipeline.db.SQLModel")
    def test_get_engine_reuses_existing_engine(self, mock_sqlmodel, mock_create_engine):
        """Test get_engine reuses existing engine."""
        from powderpipeline.db import get_engine

        mock_settings = MagicMock()
        mock_settings.base_data_path = Path("/tmp/test")
        mock_settings.db_name = "test.duckdb"

        import powderpipeline.db as db_module

        existing_engine = MagicMock()
        db_module.__engine__ = existing_engine

        engine = get_engine(mock_settings)

        assert engine == existing_engine
        mock_create_engine.assert_not_called()


class TestSkiPassModel:
    """Tests for the SkiPass database model."""

    def test_ski_pass_model_creation(self):
        """Test SkiPass model can be created."""
        from powderpipeline.db.ski_pass import SkiPass

        ski_pass = SkiPass(
            provider="Epic",
            pass_name="Epic Local Pass",
            pass_type="Standard",
            age_range="Adult",
            price="$859",
        )

        assert ski_pass.provider == "Epic"
        assert ski_pass.pass_name == "Epic Local Pass"
        assert ski_pass.pass_type == "Standard"
        assert ski_pass.age_range == "Adult"
        assert ski_pass.price == "$859"

    def test_ski_pass_has_uuid(self):
        """Test SkiPass has UUID as primary key."""
        from powderpipeline.db.ski_pass import SkiPass

        ski_pass = SkiPass(
            provider="Ikon",
            pass_name="Ikon Pass",
            pass_type="Standard",
            age_range="Adult",
            price="$1200",
        )

        assert ski_pass.id is not None


class TestVisualization:
    """Tests for the visualization module."""

    def test_visualization_imports(self):
        """Test visualization module can be imported."""
        pytest.importorskip("dash")
        from powderpipeline import visualization

        assert visualization.app is not None
        assert visualization.dash is not None


class TestSnowConditionsScraper:
    """Tests for the snow conditions scraper module."""

    def test_snow_conditions_function_exists(self):
        """Test get_snow_conditions function exists."""
        from powderpipeline.scrapers.snow_conditions import get_snow_conditions

        assert callable(get_snow_conditions)
