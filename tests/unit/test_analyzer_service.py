"""Unit tests for AnalyzerService."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.kiro_analyzer.models import LogEntry
from src.kiro_analyzer.services.analyzer_service import AnalyzerService
from src.kiro_analyzer.analyzers import (
    RequestCountCalculator,
    ResponseTimeCalculator,
    CodeGenerationCalculator,
    ToolUsageCalculator,
    ActivityPatternCalculator,
    CharacterCountCalculator
)


def create_test_entry(
    timestamp: datetime,
    event_type: str = "request",
    data: dict = None
) -> LogEntry:
    """Helper to create test log entries."""
    return LogEntry(
        timestamp=timestamp,
        event_type=event_type,
        data=data or {},
        raw_line="test",
        source_file=Path("/test/log.json")
    )


def test_analyzer_service_initialization():
    """Test that AnalyzerService can be initialized with calculators."""
    calculators = [
        RequestCountCalculator(),
        ResponseTimeCalculator()
    ]
    service = AnalyzerService(calculators)
    assert service.calculators == calculators


def test_analyze_with_empty_entries():
    """Test analyze with no log entries returns default metrics."""
    calculators = [
        RequestCountCalculator(),
        ResponseTimeCalculator(),
        CodeGenerationCalculator(),
        ToolUsageCalculator(),
        ActivityPatternCalculator(),
        CharacterCountCalculator()
    ]
    service = AnalyzerService(calculators)
    
    start_date = datetime(2025, 11, 1)
    end_date = datetime(2025, 11, 7)
    
    metrics = service.analyze([], (start_date, end_date))
    
    assert metrics.total_requests == 0
    assert metrics.total_conversations == 0
    assert metrics.avg_response_time_seconds == 0.0
    assert metrics.total_characters_processed == 0
    assert metrics.lines_of_code_generated == 0
    assert metrics.success_rate_percent == 0.0
    assert len(metrics.tool_usage) == 0
    assert len(metrics.daily_breakdown) == 0


def test_analyze_with_sample_entries():
    """Test analyze with sample log entries computes metrics correctly."""
    calculators = [
        RequestCountCalculator(),
        ResponseTimeCalculator(),
        CodeGenerationCalculator(),
        ToolUsageCalculator(),
        CharacterCountCalculator()
    ]
    service = AnalyzerService(calculators)
    
    base_time = datetime(2025, 11, 15, 10, 0, 0)
    
    entries = [
        create_test_entry(base_time, "request", {"status": "success"}),
        create_test_entry(base_time + timedelta(minutes=5), "request", {"status": "success"}),
        create_test_entry(base_time + timedelta(minutes=10), "conversation_start", {}),
        create_test_entry(
            base_time + timedelta(minutes=15),
            "request",
            {"response_time": 2.5, "lines_generated": 50, "language": "python"}
        ),
        create_test_entry(
            base_time + timedelta(minutes=20),
            "tool_invocation",
            {"tool_name": "file_read"}
        ),
        create_test_entry(
            base_time + timedelta(minutes=25),
            "request",
            {"character_count": 1000}
        )
    ]
    
    start_date = datetime(2025, 11, 15)
    end_date = datetime(2025, 11, 15, 23, 59, 59)
    
    metrics = service.analyze(entries, (start_date, end_date))
    
    # Verify basic counts
    assert metrics.total_requests == 4  # 4 request events
    assert metrics.total_conversations == 1  # 1 conversation_start event
    assert metrics.total_characters_processed == 1000
    
    # Verify response time metrics
    assert metrics.avg_response_time_seconds == 2.5
    assert metrics.fastest_response_time_seconds == 2.5
    assert metrics.slowest_response_time_seconds == 2.5
    
    # Verify code generation metrics
    assert metrics.lines_of_code_generated == 50
    assert 'python' in metrics.lines_by_language
    assert metrics.lines_by_language['python'] == 50
    
    # Verify tool usage
    assert 'file_read' in metrics.tool_usage
    assert metrics.tool_usage['file_read'] == 1



def test_analyze_handles_calculator_failures():
    """Test that analyze continues when a calculator fails."""
    
    class FailingCalculator:
        """Calculator that always raises an exception."""
        def calculate(self, entries):
            raise ValueError("Intentional failure")
    
    calculators = [
        FailingCalculator(),
        RequestCountCalculator(),  # This should still work
        FailingCalculator(),
    ]
    service = AnalyzerService(calculators)
    
    entries = [
        create_test_entry(datetime(2025, 11, 15, 10, 0), "request"),
        create_test_entry(datetime(2025, 11, 15, 10, 5), "request"),
    ]
    
    start_date = datetime(2025, 11, 15)
    end_date = datetime(2025, 11, 15, 23, 59, 59)
    
    # Should not raise an exception
    metrics = service.analyze(entries, (start_date, end_date))
    
    # Should have results from the working calculator
    assert metrics.total_requests == 2
    # Other metrics should have defaults
    assert metrics.total_conversations == 0
    assert metrics.avg_response_time_seconds == 0.0


def test_analyze_merges_nested_dictionaries():
    """Test that nested dictionaries are properly merged."""
    
    class Calculator1:
        def calculate(self, entries):
            return {
                'lines_by_language': {'python': 100, 'javascript': 50},
                'tool_usage': {'file_read': 5}
            }
    
    class Calculator2:
        def calculate(self, entries):
            return {
                'lines_by_language': {'python': 50, 'typescript': 30},
                'tool_usage': {'file_write': 3, 'file_read': 2}
            }
    
    calculators = [Calculator1(), Calculator2()]
    service = AnalyzerService(calculators)
    
    start_date = datetime(2025, 11, 15)
    end_date = datetime(2025, 11, 15, 23, 59, 59)
    
    metrics = service.analyze([], (start_date, end_date))
    
    # Verify dictionaries are merged, not replaced
    assert metrics.lines_by_language['python'] == 150  # 100 + 50
    assert metrics.lines_by_language['javascript'] == 50
    assert metrics.lines_by_language['typescript'] == 30
    
    assert metrics.tool_usage['file_read'] == 7  # 5 + 2
    assert metrics.tool_usage['file_write'] == 3


def test_analyze_handles_missing_keys():
    """Test that analyze handles calculators returning incomplete data."""
    
    class PartialCalculator:
        def calculate(self, entries):
            # Only return some metrics
            return {
                'total_requests': 10,
                'lines_by_language': {'python': 100}
            }
    
    calculators = [PartialCalculator()]
    service = AnalyzerService(calculators)
    
    start_date = datetime(2025, 11, 15)
    end_date = datetime(2025, 11, 15, 23, 59, 59)
    
    metrics = service.analyze([], (start_date, end_date))
    
    # Should have the provided metrics
    assert metrics.total_requests == 10
    assert metrics.lines_by_language['python'] == 100
    
    # Should have defaults for missing metrics
    assert metrics.total_conversations == 0
    assert metrics.avg_response_time_seconds == 0.0
    assert metrics.total_characters_processed == 0
    assert metrics.success_rate_percent == 0.0


def test_filter_by_date_range():
    """Test filtering log entries by date range."""
    service = AnalyzerService([])
    
    entries = [
        create_test_entry(datetime(2025, 11, 10, 10, 0)),
        create_test_entry(datetime(2025, 11, 15, 10, 0)),
        create_test_entry(datetime(2025, 11, 20, 10, 0)),
        create_test_entry(datetime(2025, 11, 25, 10, 0)),
    ]
    
    # Filter to middle range (inclusive on both ends)
    start_date = datetime(2025, 11, 15)
    end_date = datetime(2025, 11, 20, 23, 59, 59)  # End of day on Nov 20
    
    filtered = service.filter_by_date_range(entries, start_date, end_date)
    
    assert len(filtered) == 2
    assert filtered[0].timestamp == datetime(2025, 11, 15, 10, 0)
    assert filtered[1].timestamp == datetime(2025, 11, 20, 10, 0)


def test_filter_by_date_range_with_timezone():
    """Test filtering handles timezone-aware datetimes."""
    from datetime import timezone
    
    service = AnalyzerService([])
    
    # Create timezone-aware entries
    tz = timezone.utc
    entries = [
        create_test_entry(datetime(2025, 11, 15, 10, 0, tzinfo=tz)),
        create_test_entry(datetime(2025, 11, 16, 10, 0, tzinfo=tz)),
    ]
    
    # Filter with naive datetimes (end of day on Nov 16)
    start_date = datetime(2025, 11, 15)
    end_date = datetime(2025, 11, 16, 23, 59, 59)
    
    filtered = service.filter_by_date_range(entries, start_date, end_date)
    
    # Should handle timezone conversion and include both entries
    assert len(filtered) == 2
