"""Calculator for LLM model usage metrics."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models import LogEntry


class ModelUsageCalculator:
    """Calculate LLM model usage statistics.
    
    This calculator extracts and tracks which LLM models are being used
    by Kiro, including model selection from settings and actual usage in logs.
    """
    
    def __init__(self, kiro_user_settings_path: Optional[Path] = None):
        """Initialize with optional path to Kiro user settings.
        
        Args:
            kiro_user_settings_path: Path to Kiro User settings.json file
                Defaults to standard macOS location if not provided
        """
        if kiro_user_settings_path is None:
            self.settings_path = Path.home() / "Library/Application Support/Kiro/User/settings.json"
        else:
            self.settings_path = kiro_user_settings_path
    
    def calculate(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """Calculate model usage metrics.
        
        Args:
            entries: List of parsed log entries to analyze
            
        Returns:
            Dictionary with:
            - 'configured_model': Model from settings.json
            - 'agent_model': Agent-specific model from settings
            - 'models_used': Dict mapping model names to usage counts from logs
            - 'model_settings': Full model-related settings
        """
        # Extract configured model from settings
        model_settings = self._extract_model_from_settings()
        
        # Track model usage from log entries
        models_used = self._track_model_usage_from_logs(entries)
        
        return {
            'configured_model': model_settings.get('modelSelection'),
            'agent_model': model_settings.get('agentModelSelection'),
            'models_used': models_used,
            'model_settings': model_settings
        }
    
    def _extract_model_from_settings(self) -> Dict[str, Any]:
        """Extract model configuration from Kiro settings.json.
        
        Returns:
            Dictionary with model-related settings
        """
        model_info = {
            'modelSelection': None,
            'agentModelSelection': None,
            'agentAutonomy': None
        }
        
        try:
            if self.settings_path.exists():
                with open(self.settings_path, 'r') as f:
                    settings = json.load(f)
                
                # Extract model selection settings
                if 'kiroAgent.modelSelection' in settings:
                    model_info['modelSelection'] = settings['kiroAgent.modelSelection']
                
                if 'kiroAgent.agentModelSelection' in settings:
                    model_info['agentModelSelection'] = settings['kiroAgent.agentModelSelection']
                
                if 'kiroAgent.agentAutonomy' in settings:
                    model_info['agentAutonomy'] = settings['kiroAgent.agentAutonomy']
        
        except (json.JSONDecodeError, IOError):
            # Return empty dict if settings can't be read
            pass
        
        return model_info
    
    def _track_model_usage_from_logs(self, entries: List[LogEntry]) -> Dict[str, int]:
        """Track which models were actually used in log entries.
        
        Args:
            entries: List of log entries
            
        Returns:
            Dictionary mapping model names to usage counts
        """
        model_counts: Dict[str, int] = {}
        
        for entry in entries:
            # Look for model information in various fields
            model_name = None
            
            if 'model' in entry.data:
                model_name = entry.data['model']
            elif 'model_name' in entry.data:
                model_name = entry.data['model_name']
            elif 'llm_model' in entry.data:
                model_name = entry.data['llm_model']
            elif 'ai_model' in entry.data:
                model_name = entry.data['ai_model']
            
            # Also check nested context
            if not model_name and 'context' in entry.data:
                context = entry.data['context']
                if isinstance(context, dict):
                    model_name = context.get('model') or context.get('model_name')
            
            if model_name:
                model_counts[model_name] = model_counts.get(model_name, 0) + 1
        
        return model_counts
