"""Calculator for code generation metrics."""

from typing import Any, Dict, List

from ..models import LogEntry


class CodeGenerationCalculator:
    """Calculate code generation statistics from log entries.
    
    This calculator implements the MetricCalculator protocol to compute:
    - Total lines of code generated
    - Lines of code by programming language
    - Success rate of requests
    """
    
    def calculate(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """Calculate code generation metrics.
        
        Args:
            entries: List of parsed log entries to analyze
            
        Returns:
            Dictionary with 'lines_of_code_generated', 'lines_by_language',
            and 'success_rate_percent'
        """
        total_lines = 0
        lines_by_language: Dict[str, int] = {}
        successful_requests = 0
        failed_requests = 0
        
        for entry in entries:
            # Count lines of code generated
            if 'lines_generated' in entry.data:
                try:
                    lines = int(entry.data['lines_generated'])
                    if lines > 0:
                        total_lines += lines
                        
                        # Categorize by language if available
                        language = entry.data.get('language', 'unknown')
                        lines_by_language[language] = lines_by_language.get(language, 0) + lines
                except (ValueError, TypeError):
                    pass
            
            # Track success/failure for success rate calculation
            if entry.event_type == 'request':
                status = entry.data.get('status', '')
                if status == 'success' or entry.data.get('success', False):
                    successful_requests += 1
                elif status == 'failed' or status == 'error' or entry.data.get('failed', False):
                    failed_requests += 1
        
        # Calculate success rate
        total_tracked_requests = successful_requests + failed_requests
        if total_tracked_requests > 0:
            success_rate = (successful_requests / total_tracked_requests) * 100
        else:
            success_rate = 0.0
        
        return {
            'lines_of_code_generated': total_lines,
            'lines_by_language': lines_by_language,
            'success_rate_percent': success_rate
        }
