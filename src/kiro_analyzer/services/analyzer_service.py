"""Service for analyzing log entries and computing productivity metrics."""

from datetime import datetime
from typing import List, Tuple

from ..models import LogEntry, ProductivityMetrics
from ..protocols import MetricCalculator


class AnalyzerService:
    """Orchestrates metric calculation from log entries.
    
    This service coordinates multiple MetricCalculator instances to compute
    comprehensive productivity metrics from parsed log entries.
    
    Attributes:
        calculators: List of MetricCalculator instances to run
    """
    
    def __init__(self, calculators: List[MetricCalculator]):
        """Initialize the analyzer service.
        
        Args:
            calculators: List of MetricCalculator instances to use for analysis
        """
        self.calculators = calculators
    
    def analyze(
        self, 
        entries: List[LogEntry],
        analysis_period: Tuple[datetime, datetime]
    ) -> ProductivityMetrics:
        """Analyze log entries and compute all metrics.
        
        Runs all registered calculators and aggregates their results into
        a ProductivityMetrics object. Handles missing or incomplete data
        gracefully by setting default values.
        
        Args:
            entries: List of parsed log entries to analyze
            analysis_period: Tuple of (start_date, end_date) for the analysis
            
        Returns:
            ProductivityMetrics object with all computed metrics
        """
        # Initialize aggregated results with defaults
        aggregated = {
            'total_requests': 0,
            'total_conversations': 0,
            'avg_response_time_seconds': 0.0,
            'fastest_response_time_seconds': 0.0,
            'slowest_response_time_seconds': 0.0,
            'total_characters_processed': 0,
            'lines_of_code_generated': 0,
            'lines_by_language': {},
            'success_rate_percent': 0.0,
            'tool_usage': {},
            'peak_activity_periods': [],
            'daily_breakdown': {}
        }
        
        # Run all calculators and merge results
        for calculator in self.calculators:
            try:
                result = calculator.calculate(entries)
                # Merge results with proper handling of nested dictionaries
                self._merge_results(aggregated, result)
            except Exception as e:
                # Log the error but continue with other calculators
                # In production, this would use proper logging
                print(f"Warning: Calculator {calculator.__class__.__name__} failed: {e}")
                continue
        
        # Create ProductivityMetrics object from aggregated results
        metrics = ProductivityMetrics(
            analysis_period=analysis_period,
            total_requests=aggregated.get('total_requests', 0),
            total_conversations=aggregated.get('total_conversations', 0),
            avg_response_time_seconds=aggregated.get('avg_response_time_seconds', 0.0),
            fastest_response_time_seconds=aggregated.get('fastest_response_time_seconds', 0.0),
            slowest_response_time_seconds=aggregated.get('slowest_response_time_seconds', 0.0),
            total_characters_processed=aggregated.get('total_characters_processed', 0),
            lines_of_code_generated=aggregated.get('lines_of_code_generated', 0),
            lines_by_language=aggregated.get('lines_by_language', {}),
            success_rate_percent=aggregated.get('success_rate_percent', 0.0),
            tool_usage=aggregated.get('tool_usage', {}),
            peak_activity_periods=aggregated.get('peak_activity_periods', []),
            daily_breakdown=aggregated.get('daily_breakdown', {})
        )
        
        return metrics
    
    def _merge_results(self, aggregated: dict, result: dict) -> None:
        """Merge calculator results into aggregated metrics.
        
        Handles different data types appropriately:
        - Dictionaries are merged (not replaced)
        - Lists are replaced (not concatenated)
        - Scalar values are replaced
        
        Args:
            aggregated: The accumulated results dictionary to update
            result: New results from a calculator to merge in
        """
        for key, value in result.items():
            if key not in aggregated:
                # New key, just add it
                aggregated[key] = value
            elif isinstance(value, dict) and isinstance(aggregated[key], dict):
                # Merge dictionaries (for lines_by_language, tool_usage, daily_breakdown)
                for sub_key, sub_value in value.items():
                    if sub_key in aggregated[key]:
                        # If key exists, add values (for counts)
                        try:
                            aggregated[key][sub_key] = aggregated[key][sub_key] + sub_value
                        except (TypeError, ValueError):
                            # If addition fails, replace
                            aggregated[key][sub_key] = sub_value
                    else:
                        aggregated[key][sub_key] = sub_value
            else:
                # Replace scalar values and lists
                aggregated[key] = value
    
    def filter_by_date_range(
        self,
        entries: List[LogEntry],
        start_date: datetime,
        end_date: datetime
    ) -> List[LogEntry]:
        """Filter log entries by timestamp within date range.
        
        Filters entries to include only those with timestamps between
        start_date (inclusive) and end_date (inclusive). Handles timezone
        conversions if needed by comparing naive datetimes.
        
        Args:
            entries: List of log entries to filter
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            
        Returns:
            Filtered list of log entries within the date range
        """
        filtered = []
        
        for entry in entries:
            # Normalize timestamps for comparison
            entry_time = entry.timestamp
            
            # Convert to naive datetime if timezone-aware for comparison
            if entry_time.tzinfo is not None:
                entry_time = entry_time.replace(tzinfo=None)
            
            compare_start = start_date
            compare_end = end_date
            
            if compare_start.tzinfo is not None:
                compare_start = compare_start.replace(tzinfo=None)
            if compare_end.tzinfo is not None:
                compare_end = compare_end.replace(tzinfo=None)
            
            # Check if entry is within range (inclusive)
            if compare_start <= entry_time <= compare_end:
                filtered.append(entry)
        
        return filtered
