"""Configuration management for Kiro Activity Analyzer."""

import json
from pathlib import Path
from typing import Optional

from ..models import AnalyzerConfig


class ConfigManager:
    """Manages configuration loading and saving for the analyzer.
    
    Handles reading configuration from ~/.kiro-analyzer/config.json with
    sensible defaults for missing values or files.
    """
    
    DEFAULT_CONFIG_PATH = Path.home() / ".kiro-analyzer" / "config.json"
    DEFAULT_KIRO_APP_FOLDER = Path.home() / "Library" / "Application Support" / "Kiro"
    DEFAULT_DATE_RANGE_DAYS = 7
    DEFAULT_OUTPUT_DIR = Path.home() / ".kiro-analyzer" / "reports"
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the ConfigManager.
        
        Args:
            config_path: Optional custom path to config file. 
                        Defaults to ~/.kiro-analyzer/config.json
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
    
    def load_config(self) -> AnalyzerConfig:
        """Load configuration from file or return defaults.
        
        Reads configuration from the config file if it exists, otherwise
        returns a configuration with sensible defaults. Missing fields in
        the config file are filled with defaults.
        
        Returns:
            AnalyzerConfig object with loaded or default values
            
        Note:
            This method handles missing config files gracefully by returning
            defaults. It does not raise exceptions for missing files.
        """
        # Start with defaults
        config_data = {
            "kiro_app_folder": str(self.DEFAULT_KIRO_APP_FOLDER),
            "default_date_range_days": self.DEFAULT_DATE_RANGE_DAYS,
            "output_directory": str(self.DEFAULT_OUTPUT_DIR),
            "enabled_metrics": [],
            "custom_parsers": []
        }
        
        # Try to load from file if it exists
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    file_data = json.load(f)
                    # Update defaults with values from file
                    config_data.update(file_data)
            except (json.JSONDecodeError, IOError) as e:
                # If file is corrupted or unreadable, use defaults
                # Could log a warning here in the future
                pass
        
        # Convert string paths to Path objects
        return AnalyzerConfig(
            kiro_app_folder=Path(config_data["kiro_app_folder"]),
            default_date_range_days=config_data["default_date_range_days"],
            output_directory=Path(config_data["output_directory"]),
            enabled_metrics=config_data["enabled_metrics"],
            custom_parsers=config_data["custom_parsers"]
        )
    
    def save_config(self, config: AnalyzerConfig) -> None:
        """Save configuration to file.
        
        Persists the configuration to the config file, creating the parent
        directory if it doesn't exist.
        
        Args:
            config: AnalyzerConfig object to save
            
        Raises:
            IOError: If the config file cannot be written
        """
        # Ensure the config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert config to dictionary with string paths
        config_data = {
            "kiro_app_folder": str(config.kiro_app_folder),
            "default_date_range_days": config.default_date_range_days,
            "output_directory": str(config.output_directory),
            "enabled_metrics": config.enabled_metrics,
            "custom_parsers": config.custom_parsers
        }
        
        # Write to file with pretty formatting
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
