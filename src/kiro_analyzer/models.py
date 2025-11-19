"""Core data models for Kiro Activity Analyzer."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional


@dataclass
class LogEntry:
    """Represents a single parsed log entry.
    
    Attributes:
        timestamp: When the log entry was created
        event_type: Type of event (e.g., 'request', 'response', 'tool_invocation')
        data: Additional structured data from the log entry
        raw_line: Original unparsed log line
        source_file: Path to the log file this entry came from
    """
    timestamp: datetime
    event_type: str
    data: Dict[str, Any]
    raw_line: str
    source_file: Path


@dataclass
class LogFileMetadata:
    """Metadata about a discovered log file.
    
    Attributes:
        path: Full path to the log file
        file_type: Type of log file (e.g., 'activity', 'metrics', 'session')
        size_bytes: Size of the file in bytes
        created_at: File creation timestamp
        modified_at: File last modification timestamp
    """
    path: Path
    file_type: str
    size_bytes: int
    created_at: datetime
    modified_at: datetime


@dataclass
class ProductivityMetrics:
    """Aggregated productivity metrics from log analysis.
    
    Attributes:
        analysis_period: Tuple of (start_date, end_date) for the analysis
        total_requests: Total number of requests made to Kiro
        total_conversations: Number of conversations initiated
        avg_response_time_seconds: Average response time for operations
        fastest_response_time_seconds: Minimum response time observed
        slowest_response_time_seconds: Maximum response time observed
        total_characters_processed: Total characters processed across all requests
        lines_of_code_generated: Total lines of code generated
        lines_by_language: Dictionary mapping language names to line counts
        success_rate_percent: Percentage of successful requests
        tool_usage: Dictionary mapping tool names to usage counts
        peak_activity_periods: List of time windows with highest activity
        daily_breakdown: Dictionary mapping dates to activity counts
    """
    analysis_period: Tuple[datetime, datetime]
    total_requests: int
    total_conversations: int
    avg_response_time_seconds: float
    fastest_response_time_seconds: float
    slowest_response_time_seconds: float
    total_characters_processed: int
    lines_of_code_generated: int
    lines_by_language: Dict[str, int]
    success_rate_percent: float
    tool_usage: Dict[str, int]
    peak_activity_periods: List[Tuple[datetime, datetime]]
    daily_breakdown: Dict[str, int]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of all metrics with ISO-formatted dates
        """
        return {
            "analysis_period": {
                "start": self.analysis_period[0].isoformat(),
                "end": self.analysis_period[1].isoformat()
            },
            "total_requests": self.total_requests,
            "total_conversations": self.total_conversations,
            "avg_response_time_seconds": self.avg_response_time_seconds,
            "fastest_response_time_seconds": self.fastest_response_time_seconds,
            "slowest_response_time_seconds": self.slowest_response_time_seconds,
            "total_characters_processed": self.total_characters_processed,
            "lines_of_code_generated": self.lines_of_code_generated,
            "lines_by_language": self.lines_by_language,
            "success_rate_percent": self.success_rate_percent,
            "tool_usage": self.tool_usage,
            "peak_activity_periods": [
                [start.isoformat(), end.isoformat()]
                for start, end in self.peak_activity_periods
            ],
            "daily_breakdown": self.daily_breakdown
        }
    
    def to_csv_rows(self) -> List[Dict[str, Any]]:
        """Convert metrics to rows for CSV output.
        
        Returns:
            List of dictionaries with metric_name, value, and unit columns
        """
        rows = [
            {"metric_name": "total_requests", "value": self.total_requests, "unit": "count"},
            {"metric_name": "total_conversations", "value": self.total_conversations, "unit": "count"},
            {"metric_name": "avg_response_time", "value": self.avg_response_time_seconds, "unit": "seconds"},
            {"metric_name": "fastest_response_time", "value": self.fastest_response_time_seconds, "unit": "seconds"},
            {"metric_name": "slowest_response_time", "value": self.slowest_response_time_seconds, "unit": "seconds"},
            {"metric_name": "total_characters_processed", "value": self.total_characters_processed, "unit": "characters"},
            {"metric_name": "lines_of_code_generated", "value": self.lines_of_code_generated, "unit": "lines"},
            {"metric_name": "success_rate", "value": self.success_rate_percent, "unit": "percent"},
        ]
        
        # Add lines by language as separate rows
        for language, count in self.lines_by_language.items():
            rows.append({
                "metric_name": f"lines_of_code_{language}",
                "value": count,
                "unit": "lines"
            })
        
        # Add tool usage as separate rows
        for tool_name, count in self.tool_usage.items():
            rows.append({
                "metric_name": f"tool_usage_{tool_name}",
                "value": count,
                "unit": "count"
            })
        
        # Add daily breakdown as separate rows
        for date_str, count in self.daily_breakdown.items():
            rows.append({
                "metric_name": f"daily_activity_{date_str}",
                "value": count,
                "unit": "count"
            })
        
        return rows


@dataclass
class AnalyzerConfig:
    """Configuration settings for the analyzer.
    
    Attributes:
        kiro_app_folder: Path to the Kiro application folder containing logs
        default_date_range_days: Default number of days to analyze if not specified
        output_directory: Directory where reports should be saved
        enabled_metrics: List of metric names to calculate (empty = all)
        custom_parsers: List of custom parser class paths to load
    """
    kiro_app_folder: Path
    default_date_range_days: int = 7
    output_directory: Path = field(default_factory=lambda: Path.home() / ".kiro-analyzer" / "reports")
    enabled_metrics: List[str] = field(default_factory=list)
    custom_parsers: List[str] = field(default_factory=list)
