"""Unit tests for log parsers."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from kiro_analyzer.parsers import (
    JSONLogParser,
    PlainTextLogParser,
    ParserRegistry,
    ParserService
)
from kiro_analyzer.models import LogEntry


class TestJSONLogParser:
    """Tests for JSONLogParser."""
    
    def test_can_parse_json_file(self):
        """Test that parser recognizes .json files."""
        parser = JSONLogParser()
        assert parser.can_parse(Path("test.json"))
        assert parser.can_parse(Path("test.jsonl"))
    
    def test_can_parse_json_log_file(self, tmp_path):
        """Test that parser recognizes .log files with JSON content."""
        parser = JSONLogParser()
        log_file = tmp_path / "test.log"
        log_file.write_text('{"timestamp": "2025-11-19T10:00:00Z", "event": "test"}')
        assert parser.can_parse(log_file)
    
    def test_parse_valid_json_entries(self, tmp_path):
        """Test parsing valid JSON log entries."""
        parser = JSONLogParser()
        log_file = tmp_path / "test.json"
        
        # Create test log file
        entries = [
            {"timestamp": "2025-11-19T10:00:00Z", "event_type": "request", "message": "Test 1"},
            {"timestamp": "2025-11-19T10:01:00Z", "event_type": "response", "message": "Test 2"}
        ]
        log_file.write_text('\n'.join(json.dumps(e) for e in entries))
        
        # Parse and verify
        parsed = list(parser.parse(log_file))
        assert len(parsed) == 2
        assert parsed[0].event_type == "request"
        assert parsed[1].event_type == "response"
        assert parsed[0].timestamp.year == 2025
    
    def test_parse_handles_malformed_json(self, tmp_path):
        """Test that parser handles malformed JSON gracefully."""
        parser = JSONLogParser()
        log_file = tmp_path / "test.json"
        
        # Mix valid and invalid entries
        log_file.write_text(
            '{"timestamp": "2025-11-19T10:00:00Z", "event": "valid"}\n'
            '{invalid json}\n'
            '{"timestamp": "2025-11-19T10:02:00Z", "event": "also_valid"}\n'
        )
        
        # Should parse valid entries and skip invalid
        parsed = list(parser.parse(log_file))
        assert len(parsed) == 2
        assert parsed[0].event_type == "valid"
        assert parsed[1].event_type == "also_valid"


class TestPlainTextLogParser:
    """Tests for PlainTextLogParser."""
    
    def test_can_parse_log_file(self):
        """Test that parser recognizes .log and .txt files."""
        parser = PlainTextLogParser()
        assert parser.can_parse(Path("test.log"))
        assert parser.can_parse(Path("test.txt"))
    
    def test_parse_bracketed_format(self, tmp_path):
        """Test parsing bracketed log format."""
        parser = PlainTextLogParser()
        log_file = tmp_path / "test.log"
        
        log_file.write_text(
            "[2025-11-19T10:00:00Z] [INFO] Test message 1\n"
            "[2025-11-19T10:01:00Z] [ERROR] Test message 2\n"
        )
        
        parsed = list(parser.parse(log_file))
        assert len(parsed) == 2
        assert parsed[0].event_type == "INFO"
        assert parsed[1].event_type == "ERROR"
    
    def test_parse_colon_format(self, tmp_path):
        """Test parsing colon-separated log format."""
        parser = PlainTextLogParser()
        log_file = tmp_path / "test.log"
        
        log_file.write_text(
            "2025-11-19T10:00:00Z INFO: Test message 1\n"
            "2025-11-19T10:01:00Z ERROR: Test message 2\n"
        )
        
        parsed = list(parser.parse(log_file))
        assert len(parsed) == 2
        assert parsed[0].event_type == "INFO"
        assert parsed[1].event_type == "ERROR"


class TestParserRegistry:
    """Tests for ParserRegistry."""
    
    def test_register_and_get_parser(self):
        """Test registering and retrieving parsers."""
        registry = ParserRegistry()
        json_parser = JSONLogParser()
        
        registry.register_parser(json_parser)
        
        # Should return JSON parser for .json files
        parser = registry.get_parser(Path("test.json"))
        assert isinstance(parser, JSONLogParser)
    
    def test_get_parser_returns_none_for_unknown_file(self):
        """Test that registry returns None for unsupported files."""
        registry = ParserRegistry()
        parser = registry.get_parser(Path("test.xyz"))
        assert parser is None


class TestParserService:
    """Tests for ParserService."""
    
    def test_parse_file_with_json(self, tmp_path):
        """Test parsing a JSON file through the service."""
        service = ParserService()
        log_file = tmp_path / "test.json"
        
        entries = [
            {"timestamp": "2025-11-19T10:00:00Z", "event": "test1"},
            {"timestamp": "2025-11-19T10:01:00Z", "event": "test2"}
        ]
        log_file.write_text('\n'.join(json.dumps(e) for e in entries))
        
        parsed = service.parse_file(log_file)
        assert len(parsed) == 2
    
    def test_parse_file_raises_for_missing_file(self):
        """Test that service raises error for missing files."""
        service = ParserService()
        with pytest.raises(FileNotFoundError):
            service.parse_file(Path("/nonexistent/file.json"))
    
    def test_parse_files_aggregates_entries(self, tmp_path):
        """Test parsing multiple files."""
        service = ParserService()
        
        # Create two log files
        file1 = tmp_path / "test1.json"
        file1.write_text('{"timestamp": "2025-11-19T10:00:00Z", "event": "test1"}')
        
        file2 = tmp_path / "test2.json"
        file2.write_text('{"timestamp": "2025-11-19T10:01:00Z", "event": "test2"}')
        
        parsed = service.parse_files([file1, file2])
        assert len(parsed) == 2
