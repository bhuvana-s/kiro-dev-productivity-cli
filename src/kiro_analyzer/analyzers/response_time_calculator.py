"""Calculator for response time metrics."""

from typing import Any, Dict, List

from ..models import LogEntry


class ResponseTimeCalculator:
    """Calculate response time statistics from agentic mode operations.
    
    This calculator implements the MetricCalculator protocol to compute:
    - Average response time
    - Minimum (fastest) response time
    - Maximum (slowest) response time
    """
    
    def calculate(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """Calculate response time metrics.
        
        Extracts response times from log entries and computes statistics.
        Handles missing or invalid response time data gracefully.
        
        Args:
            entries: List of parsed log entries to analyze
            
        Returns:
            Dictionary with 'avg_response_time_seconds', 
            'fastest_response_time_seconds', and 'slowest_response_time_seconds'
        """
        response_times = []
        
        for entry in entries:
            # Look for response time in the data field
            if 'response_time' in entry.data:
                try:
                    response_time = float(entry.data['response_time'])
                    if response_time >= 0:  # Validate non-negative
                        response_times.append(response_time)
                except (ValueError, TypeError):
                    # Skip invalid response time data
                    continue
            elif 'response_time_seconds' in entry.data:
                try:
                    response_time = float(entry.data['response_time_seconds'])
                    if response_time >= 0:
                        response_times.append(response_time)
                except (ValueError, TypeError):
                    continue
        
        # Calculate statistics or return defaults if no valid data
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            fastest_response_time = min(response_times)
            slowest_response_time = max(response_times)
        else:
            avg_response_time = 0.0
            fastest_response_time = 0.0
            slowest_response_time = 0.0
        
        return {
            'avg_response_time_seconds': avg_response_time,
            'fastest_response_time_seconds': fastest_response_time,
            'slowest_response_time_seconds': slowest_response_time
        }
