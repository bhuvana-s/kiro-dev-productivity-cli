"""Calculator for activity pattern metrics."""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

from ..models import LogEntry


class ActivityPatternCalculator:
    """Calculate activity pattern statistics from log entries.
    
    This calculator implements the MetricCalculator protocol to analyze:
    - Peak activity periods (2-hour windows with highest activity)
    - Daily breakdown of activity counts
    """
    
    def calculate(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """Calculate activity pattern metrics.
        
        Args:
            entries: List of parsed log entries to analyze
            
        Returns:
            Dictionary with 'peak_activity_periods' and 'daily_breakdown'
        """
        if not entries:
            return {
                'peak_activity_periods': [],
                'daily_breakdown': {}
            }
        
        # Generate daily breakdown
        daily_breakdown = self._calculate_daily_breakdown(entries)
        
        # Identify peak activity periods (2-hour windows)
        peak_periods = self._identify_peak_periods(entries)
        
        return {
            'peak_activity_periods': peak_periods,
            'daily_breakdown': daily_breakdown
        }
    
    def _calculate_daily_breakdown(self, entries: List[LogEntry]) -> Dict[str, int]:
        """Generate daily activity counts.
        
        Args:
            entries: List of log entries
            
        Returns:
            Dictionary mapping date strings (YYYY-MM-DD) to activity counts
        """
        daily_counts: Dict[str, int] = defaultdict(int)
        
        for entry in entries:
            date_str = entry.timestamp.strftime('%Y-%m-%d')
            daily_counts[date_str] += 1
        
        return dict(daily_counts)
    
    def _identify_peak_periods(
        self, 
        entries: List[LogEntry], 
        window_hours: int = 2,
        top_n: int = 3
    ) -> List[Tuple[datetime, datetime]]:
        """Identify time windows with highest activity.
        
        Args:
            entries: List of log entries
            window_hours: Size of the time window in hours
            top_n: Number of peak periods to return
            
        Returns:
            List of tuples (start_time, end_time) for peak periods
        """
        if not entries:
            return []
        
        # Sort entries by timestamp
        sorted_entries = sorted(entries, key=lambda e: e.timestamp)
        
        # Find the overall time range
        min_time = sorted_entries[0].timestamp
        max_time = sorted_entries[-1].timestamp
        
        # Create 2-hour windows and count activities
        window_delta = timedelta(hours=window_hours)
        window_counts: List[Tuple[datetime, datetime, int]] = []
        
        current_time = min_time.replace(minute=0, second=0, microsecond=0)
        
        while current_time <= max_time:
            window_end = current_time + window_delta
            
            # Count entries in this window
            count = sum(
                1 for entry in sorted_entries
                if current_time <= entry.timestamp < window_end
            )
            
            if count > 0:
                window_counts.append((current_time, window_end, count))
            
            # Move to next window (1-hour step for overlapping windows)
            current_time += timedelta(hours=1)
        
        # Sort by count (descending) and take top N
        window_counts.sort(key=lambda x: x[2], reverse=True)
        
        # Return top N periods without the count
        peak_periods = [
            (start, end) for start, end, _ in window_counts[:top_n]
        ]
        
        return peak_periods
