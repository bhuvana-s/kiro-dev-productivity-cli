"""Unit tests for ConfigManager."""

import json
import tempfile
from pathlib import Path

import pytest

from kiro_analyzer.models import AnalyzerConfig
from kiro_analyzer.services import ConfigManager


class TestConfigManager:
    """Test suite for ConfigManager class."""
    
    def test_load_config_with_missing_file_returns_defaults(self):
        """Test that loading config with missing file returns default values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nonexistent" / "config.json"
            manager = ConfigManager(config_path)
            
            config = manager.load_config()
            
            assert isinstance(config, AnalyzerConfig)
            assert config.kiro_app_folder == ConfigManager.DEFAULT_KIRO_APP_FOLDER
            assert config.default_date_range_days == ConfigManager.DEFAULT_DATE_RANGE_DAYS
            assert config.output_directory == ConfigManager.DEFAULT_OUTPUT_DIR
            assert config.enabled_metrics == []
            assert config.custom_parsers == []
    
    def test_load_config_with_valid_file(self):
        """Test loading configuration from a valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            
            # Create a config file
            test_config = {
                "kiro_app_folder": "/custom/path/to/kiro",
                "default_date_range_days": 14,
                "output_directory": "/custom/output",
                "enabled_metrics": ["metric1", "metric2"],
                "custom_parsers": ["parser.CustomParser"]
            }
            
            with open(config_path, 'w') as f:
                json.dump(test_config, f)
            
            manager = ConfigManager(config_path)
            config = manager.load_config()
            
            assert config.kiro_app_folder == Path("/custom/path/to/kiro")
            assert config.default_date_range_days == 14
            assert config.output_directory == Path("/custom/output")
            assert config.enabled_metrics == ["metric1", "metric2"]
            assert config.custom_parsers == ["parser.CustomParser"]
    
    def test_load_config_with_partial_file_uses_defaults(self):
        """Test that missing fields in config file are filled with defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            
            # Create a partial config file
            partial_config = {
                "kiro_app_folder": "/custom/path",
                "default_date_range_days": 30
            }
            
            with open(config_path, 'w') as f:
                json.dump(partial_config, f)
            
            manager = ConfigManager(config_path)
            config = manager.load_config()
            
            # Custom values should be loaded
            assert config.kiro_app_folder == Path("/custom/path")
            assert config.default_date_range_days == 30
            
            # Missing values should use defaults
            assert config.output_directory == ConfigManager.DEFAULT_OUTPUT_DIR
            assert config.enabled_metrics == []
            assert config.custom_parsers == []
    
    def test_load_config_with_corrupted_file_returns_defaults(self):
        """Test that corrupted JSON file results in default config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            
            # Create a corrupted JSON file
            with open(config_path, 'w') as f:
                f.write("{ invalid json content }")
            
            manager = ConfigManager(config_path)
            config = manager.load_config()
            
            # Should return defaults when file is corrupted
            assert config.kiro_app_folder == ConfigManager.DEFAULT_KIRO_APP_FOLDER
            assert config.default_date_range_days == ConfigManager.DEFAULT_DATE_RANGE_DAYS
    
    def test_save_config_creates_directory(self):
        """Test that save_config creates parent directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "new_dir" / "config.json"
            manager = ConfigManager(config_path)
            
            config = AnalyzerConfig(
                kiro_app_folder=Path("/test/path"),
                default_date_range_days=10,
                output_directory=Path("/test/output")
            )
            
            manager.save_config(config)
            
            assert config_path.exists()
            assert config_path.parent.exists()
    
    def test_save_config_writes_correct_data(self):
        """Test that save_config writes configuration correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            manager = ConfigManager(config_path)
            
            config = AnalyzerConfig(
                kiro_app_folder=Path("/test/kiro"),
                default_date_range_days=21,
                output_directory=Path("/test/reports"),
                enabled_metrics=["metric1", "metric2"],
                custom_parsers=["custom.Parser"]
            )
            
            manager.save_config(config)
            
            # Read back and verify
            with open(config_path, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data["kiro_app_folder"] == "/test/kiro"
            assert saved_data["default_date_range_days"] == 21
            assert saved_data["output_directory"] == "/test/reports"
            assert saved_data["enabled_metrics"] == ["metric1", "metric2"]
            assert saved_data["custom_parsers"] == ["custom.Parser"]
    
    def test_save_and_load_roundtrip(self):
        """Test that saving and loading config preserves all data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            manager = ConfigManager(config_path)
            
            original_config = AnalyzerConfig(
                kiro_app_folder=Path("/original/kiro"),
                default_date_range_days=15,
                output_directory=Path("/original/output"),
                enabled_metrics=["m1", "m2", "m3"],
                custom_parsers=["p1", "p2"]
            )
            
            manager.save_config(original_config)
            loaded_config = manager.load_config()
            
            assert loaded_config.kiro_app_folder == original_config.kiro_app_folder
            assert loaded_config.default_date_range_days == original_config.default_date_range_days
            assert loaded_config.output_directory == original_config.output_directory
            assert loaded_config.enabled_metrics == original_config.enabled_metrics
            assert loaded_config.custom_parsers == original_config.custom_parsers
    
    def test_default_config_path_uses_home_directory(self):
        """Test that default config path is in user's home directory."""
        manager = ConfigManager()
        
        expected_path = Path.home() / ".kiro-analyzer" / "config.json"
        assert manager.config_path == expected_path
    
    def test_default_kiro_app_folder_is_macos_path(self):
        """Test that default Kiro app folder is set to macOS location."""
        expected_path = Path.home() / "Library" / "Application Support" / "Kiro"
        assert ConfigManager.DEFAULT_KIRO_APP_FOLDER == expected_path
