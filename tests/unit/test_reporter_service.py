"""Unit tests for ReporterService."""

import json
import csv
from datetime import datetime
from pathlib import Path
from io import StringIO

import pytest

from kiro_analyzer.models import ProductivityMetrics
from kiro_analyzer.reporters import ReporterService, ReportFormat


@pytest.fixture
def sample_metrics():
    """Create sample productivity metrics for testing."""
    return ProductivityMetrics(
        analysis_period=(
            datetime(2025, 11, 12, 0, 0, 0),
            datetime(2025, 11, 19, 23, 59, 59)
        ),
        total_requests=150,
        total_conversations=25,
        avg_response_time_seconds=2.5,
        fastest_response_time_seconds=0.8,
        slowest_response_time_seconds=8.2,
        total_characters_processed=45000,
        lines_of_code_generated=1200,
        lines_by_language={"python": 800, "javascript": 300, "typescript": 100},
        success_rate_percent=92.5,
        tool_usage={"file_read": 45, "file_write": 30, "bash_execute": 20},
        peak_activity_periods=[
            (datetime(2025, 11, 15, 14, 0, 0), datetime(2025, 11, 15, 16, 0, 0)),
            (datetime(2025, 11, 18, 10, 0, 0), datetime(2025, 11, 18, 12, 0, 0))
        ],
        daily_breakdown={"2025-11-12": 18, "2025-11-13": 22, "2025-11-14": 15}
    )


def test_generate_json_report(sample_metrics):
    """Test JSON report generation."""
    reporter = ReporterService()
    report = reporter.generate_report(sample_metrics, ReportFormat.JSON)
    
    # Verify it's valid JSON
    data = json.loads(report)
    
    # Check structure
    assert "generated_at" in data
    assert "analysis_period" in data
    assert "metrics" in data
    
    # Check metrics content
    metrics = data["metrics"]
    assert metrics["total_requests"] == 150
    assert metrics["total_conversations"] == 25
    assert metrics["avg_response_time_seconds"] == 2.5
    assert metrics["lines_of_code_generated"] == 1200
    assert metrics["success_rate_percent"] == 92.5


def test_generate_csv_report(sample_metrics):
    """Test CSV report generation."""
    reporter = ReporterService()
    report = reporter.generate_report(sample_metrics, ReportFormat.CSV)
    
    # Parse CSV
    reader = csv.DictReader(StringIO(report))
    rows = list(reader)
    
    # Verify header
    assert rows[0].keys() == {"metric_name", "value", "unit"}
    
    # Check some key metrics are present
    metric_names = [row["metric_name"] for row in rows]
    assert "total_requests" in metric_names
    assert "total_conversations" in metric_names
    assert "lines_of_code_generated" in metric_names
    
    # Verify nested data is expanded
    assert "lines_of_code_python" in metric_names
    assert "tool_usage_file_read" in metric_names


def test_generate_console_report(sample_metrics):
    """Test console report generation."""
    reporter = ReporterService()
    report = reporter.generate_report(sample_metrics, ReportFormat.CONSOLE)
    
    # Verify it contains expected content
    assert "Kiro Activity Analysis Report" in report
    assert "Summary Statistics" in report
    assert "Total Requests" in report
    assert "150" in report
    # Check for language data (may be split across lines with formatting)
    assert "python" in report
    assert "800" in report


def test_save_report(sample_metrics, tmp_path):
    """Test saving report to file."""
    reporter = ReporterService()
    output_path = tmp_path / "test_report.json"
    
    report = reporter.generate_report(sample_metrics, ReportFormat.JSON, output_path)
    
    # Verify file was created
    assert output_path.exists()
    
    # Verify content matches
    saved_content = output_path.read_text()
    assert saved_content == report


def test_generate_timestamped_filename():
    """Test timestamped filename generation."""
    reporter = ReporterService()
    
    filename = reporter.generate_timestamped_filename("report", ReportFormat.JSON)
    
    # Verify format
    assert filename.name.startswith("report_")
    assert filename.name.endswith(".json")
    assert filename.parent == Path.home() / ".kiro-analyzer" / "reports"


def test_unsupported_format_raises_error(sample_metrics):
    """Test that unsupported format raises ValueError."""
    reporter = ReporterService()
    
    with pytest.raises(ValueError, match="Unsupported report format"):
        # Create a mock enum value that's not supported
        class FakeFormat:
            pass
        reporter.generate_report(sample_metrics, FakeFormat())
