"""Unit tests for model usage calculator."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from kiro_analyzer.analyzers import ModelUsageCalculator
from kiro_analyzer.models import LogEntry


class TestModelUsageCalculator:
    """Tests for ModelUsageCalculator."""
    
    def test_extract_model_from_settings(self):
        """Test extracting model configuration from settings.json."""
        # Create a temporary settings file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            settings = {
                'kiroAgent.modelSelection': 'claude-sonnet-4.5',
                'kiroAgent.agentModelSelection': 'CLAUDE_SONNET_4_20250514_V1_0',
                'kiroAgent.agentAutonomy': 'Supervised'
            }
            json.dump(settings, f)
            temp_path = Path(f.name)
        
        try:
            calculator = ModelUsageCalculator(kiro_user_settings_path=temp_path)
            result = calculator.calculate([])
            
            assert result['configured_model'] == 'claude-sonnet-4.5'
            assert result['agent_model'] == 'CLAUDE_SONNET_4_20250514_V1_0'
            assert result['model_settings']['agentAutonomy'] == 'Supervised'
        finally:
            temp_path.unlink()
    
    def test_track_model_usage_from_logs(self):
        """Test tracking model usage from log entries."""
        entries = [
            LogEntry(
                timestamp=datetime.now(),
                event_type='request',
                data={'model': 'claude-sonnet-4.5'},
                raw_line='',
                source_file=Path('test.log')
            ),
            LogEntry(
                timestamp=datetime.now(),
                event_type='request',
                data={'model': 'claude-sonnet-4.5'},
                raw_line='',
                source_file=Path('test.log')
            ),
            LogEntry(
                timestamp=datetime.now(),
                event_type='request',
                data={'model': 'gpt-4'},
                raw_line='',
                source_file=Path('test.log')
            ),
        ]
        
        calculator = ModelUsageCalculator()
        result = calculator.calculate(entries)
        
        assert result['models_used']['claude-sonnet-4.5'] == 2
        assert result['models_used']['gpt-4'] == 1
    
    def test_handle_missing_settings_file(self):
        """Test handling when settings.json doesn't exist."""
        non_existent_path = Path('/tmp/non_existent_settings.json')
        calculator = ModelUsageCalculator(kiro_user_settings_path=non_existent_path)
        result = calculator.calculate([])
        
        assert result['configured_model'] is None
        assert result['agent_model'] is None
    
    def test_extract_model_from_nested_context(self):
        """Test extracting model from nested context in logs."""
        entries = [
            LogEntry(
                timestamp=datetime.now(),
                event_type='request',
                data={'context': {'model': 'claude-opus'}},
                raw_line='',
                source_file=Path('test.log')
            ),
        ]
        
        calculator = ModelUsageCalculator()
        result = calculator.calculate(entries)
        
        assert result['models_used']['claude-opus'] == 1
    
    def test_multiple_model_field_names(self):
        """Test handling different field names for model information."""
        entries = [
            LogEntry(
                timestamp=datetime.now(),
                event_type='request',
                data={'model_name': 'model-a'},
                raw_line='',
                source_file=Path('test.log')
            ),
            LogEntry(
                timestamp=datetime.now(),
                event_type='request',
                data={'llm_model': 'model-b'},
                raw_line='',
                source_file=Path('test.log')
            ),
            LogEntry(
                timestamp=datetime.now(),
                event_type='request',
                data={'ai_model': 'model-c'},
                raw_line='',
                source_file=Path('test.log')
            ),
        ]
        
        calculator = ModelUsageCalculator()
        result = calculator.calculate(entries)
        
        assert result['models_used']['model-a'] == 1
        assert result['models_used']['model-b'] == 1
        assert result['models_used']['model-c'] == 1
