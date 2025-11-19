"""Calculator for request and conversation counts."""

from typing import Any, Dict, List

from ..models import LogEntry


class RequestCountCalculator:
    """Calculate total requests and conversations from log entries.
    
    This calculator implements the MetricCalculator protocol to count:
    - Total requests (event_type='request')
    - Total conversations (event_type='conversation_start')
    """
    
    def calculate(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """Calculate request and conversation counts.
        
        Args:
            entries: List of parsed log entries to analyze
            
        Returns:
            Dictionary with 'total_requests' and 'total_conversations' keys
        """
        total_requests = 0
        total_conversations = 0
        
        for entry in entries:
            if entry.event_type == 'request':
                total_requests += 1
            elif entry.event_type == 'conversation_start':
                total_conversations += 1
        
        return {
            'total_requests': total_requests,
            'total_conversations': total_conversations
        }
