"""Unit tests for metric calculators using real Kiro log data."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from kiro_analyzer.analyzers import (
    ActivityPatternCalculator,
    CharacterCountCalculator,
    CodeGenerationCalculator,
    RequestCountCalculator,
    ResponseTimeCalculator,
    ToolUsageCalculator,
)
from kiro_analyzer.parsers import ParserService


# Path to real Kiro application folder
KIRO_APP_FOLDER = Path("/Users/bsubramani/Library/Application Support/Kiro")


@pytest.fixture
def real_log_entries():
    """Fixture to load real log entries from Kiro logs."""
    if not KIRO_APP_FOLDER.exists():
        pytest.skip("Kiro application folder not found")
    
    # Find the most recent Kiro log
    log_dirs = list(KIRO_APP_FOLDER.glob("logs/*/window*/exthost/kiro.kiroAgent"))
    if not log_dirs:
        pytest.skip("No Kiro agent log directories found")
    
    log_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    recent_dir = log_dirs[0]
    
    kiro_log = recent_dir / "Kiro Logs.log"
    if not kiro_log.exists():
        pytest.skip("Kiro Logs.log not found")
    
    # Parse the log file
    service = ParserService()
    entries = service.parse_file(kiro_log)
    
    if not entries:
        pytest.skip("No entries parsed from Kiro log")
    
    return entries


@pytest.mark.skipif(not KIRO_APP_FOLDER.exists(), reason="Kiro application folder not found")
class TestRequestCountCalculator:
    """Tests for RequestCountCalculator using real data."""
    
    def test_count_requests_and_conversations_from_real_logs(self, real_log_entries):
        """Test counting requests and conversations from real Kiro logs."""
        calculator = RequestCountCalculator()
        result = calculator.calculate(real_log_entries)
        
        print(f"\n✓ Total requests: {result['total_requests']}")
        print(f"✓ Total conversations: {result['total_conversations']}")
        
        # Verify the result structure
        assert 'total_requests' in result
        assert 'total_conversations' in result
        assert isinstance(result['total_requests'], int)
        assert isinstance(result['total_conversations'], int)
        assert result['total_requests'] >= 0
        assert result['total_conversations'] >= 0
    
    def test_empty_entries(self):
        """Test with no entries."""
        calculator = RequestCountCalculator()
        result = calculator.calculate([])
        
        assert result['total_requests'] == 0
        assert result['total_conversations'] == 0


@pytest.mark.skipif(not KIRO_APP_FOLDER.exists(), reason="Kiro application folder not found")
class TestResponseTimeCalculator:
    """Tests for ResponseTimeCalculator using real data."""
    
    def test_calculate_response_times_from_real_logs(self, real_log_entries):
        """Test calculating response time statistics from real Kiro logs."""
        calculator = ResponseTimeCalculator()
        result = calculator.calculate(real_log_entries)
        
        print(f"\n✓ Average response time: {result['avg_response_time_seconds']:.2f}s")
        print(f"✓ Fastest response time: {result['fastest_response_time_seconds']:.2f}s")
        print(f"✓ Slowest response time: {result['slowest_response_time_seconds']:.2f}s")
        
        # Verify the result structure
        assert 'avg_response_time_seconds' in result
        assert 'fastest_response_time_seconds' in result
        assert 'slowest_response_time_seconds' in result
        assert isinstance(result['avg_response_time_seconds'], float)
        assert isinstance(result['fastest_response_time_seconds'], float)
        assert isinstance(result['slowest_response_time_seconds'], float)
        assert result['avg_response_time_seconds'] >= 0.0
        assert result['fastest_response_time_seconds'] >= 0.0
        assert result['slowest_response_time_seconds'] >= 0.0
        
        # If we have response times, verify relationships
        if result['avg_response_time_seconds'] > 0:
            assert result['fastest_response_time_seconds'] <= result['avg_response_time_seconds']
            assert result['avg_response_time_seconds'] <= result['slowest_response_time_seconds']


@pytest.mark.skipif(not KIRO_APP_FOLDER.exists(), reason="Kiro application folder not found")
class TestCodeGenerationCalculator:
    """Tests for CodeGenerationCalculator using real data."""
    
    def test_calculate_code_generation_metrics_from_real_logs(self, real_log_entries):
        """Test calculating code generation statistics from real Kiro logs."""
        calculator = CodeGenerationCalculator()
        result = calculator.calculate(real_log_entries)
        
        print(f"\n✓ Total lines of code generated: {result['lines_of_code_generated']}")
        print(f"✓ Success rate: {result['success_rate_percent']:.2f}%")
        
        if result['lines_by_language']:
            print("✓ Lines by language:")
            for lang, count in sorted(result['lines_by_language'].items(), key=lambda x: x[1], reverse=True):
                print(f"  - {lang}: {count}")
        
        # Verify the result structure
        assert 'lines_of_code_generated' in result
        assert 'lines_by_language' in result
        assert 'success_rate_percent' in result
        assert isinstance(result['lines_of_code_generated'], int)
        assert isinstance(result['lines_by_language'], dict)
        assert isinstance(result['success_rate_percent'], float)
        assert result['lines_of_code_generated'] >= 0
        assert 0.0 <= result['success_rate_percent'] <= 100.0


@pytest.mark.skipif(not KIRO_APP_FOLDER.exists(), reason="Kiro application folder not found")
class TestToolUsageCalculator:
    """Tests for ToolUsageCalculator using real data."""
    
    def test_count_tool_usage_from_real_logs(self, real_log_entries):
        """Test counting tool invocations from real Kiro logs."""
        calculator = ToolUsageCalculator()
        result = calculator.calculate(real_log_entries)
        
        print(f"\n✓ Tool usage statistics:")
        if result['tool_usage']:
            for tool, count in sorted(result['tool_usage'].items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  - {tool}: {count}")
        else:
            print("  (No tool usage found in logs)")
        
        # Verify the result structure
        assert 'tool_usage' in result
        assert isinstance(result['tool_usage'], dict)
        
        # All counts should be positive integers
        for tool, count in result['tool_usage'].items():
            assert isinstance(tool, str)
            assert isinstance(count, int)
            assert count > 0


@pytest.mark.skipif(not KIRO_APP_FOLDER.exists(), reason="Kiro application folder not found")
class TestActivityPatternCalculator:
    """Tests for ActivityPatternCalculator using real data."""
    
    def test_activity_patterns_from_real_logs(self, real_log_entries):
        """Test analyzing activity patterns from real Kiro logs."""
        calculator = ActivityPatternCalculator()
        result = calculator.calculate(real_log_entries)
        
        print(f"\n✓ Daily breakdown:")
        if result['daily_breakdown']:
            for date, count in sorted(result['daily_breakdown'].items())[:7]:  # Show first 7 days
                print(f"  - {date}: {count} activities")
        
        print(f"\n✓ Peak activity periods:")
        if result['peak_activity_periods']:
            for i, (start, end) in enumerate(result['peak_activity_periods'][:3], 1):
                print(f"  {i}. {start.strftime('%Y-%m-%d %H:%M')} - {end.strftime('%H:%M')}")
        else:
            print("  (No peak periods identified)")
        
        # Verify the result structure
        assert 'daily_breakdown' in result
        assert 'peak_activity_periods' in result
        assert isinstance(result['daily_breakdown'], dict)
        assert isinstance(result['peak_activity_periods'], list)
        
        # Verify daily breakdown format
        for date_str, count in result['daily_breakdown'].items():
            assert isinstance(date_str, str)
            assert isinstance(count, int)
            assert count > 0
            # Verify date format YYYY-MM-DD
            datetime.strptime(date_str, '%Y-%m-%d')
        
        # Verify peak periods format
        for start, end in result['peak_activity_periods']:
            assert isinstance(start, datetime)
            assert isinstance(end, datetime)
            assert start < end


@pytest.mark.skipif(not KIRO_APP_FOLDER.exists(), reason="Kiro application folder not found")
class TestCharacterCountCalculator:
    """Tests for CharacterCountCalculator using real data."""
    
    def test_count_characters_from_real_logs(self, real_log_entries):
        """Test counting total characters processed from real Kiro logs."""
        calculator = CharacterCountCalculator()
        result = calculator.calculate(real_log_entries)
        
        print(f"\n✓ Total characters processed: {result['total_characters_processed']:,}")
        
        # Verify the result structure
        assert 'total_characters_processed' in result
        assert isinstance(result['total_characters_processed'], int)
        assert result['total_characters_processed'] >= 0
