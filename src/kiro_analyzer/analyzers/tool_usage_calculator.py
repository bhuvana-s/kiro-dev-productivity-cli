"""Calculator for tool usage metrics."""

from typing import Any, Dict, List

from ..models import LogEntry


class ToolUsageCalculator:
    """Calculate tool usage statistics from log entries.
    
    This calculator implements the MetricCalculator protocol to track:
    - Tool invocations
    - Frequency of each tool usage
    """
    
    def calculate(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """Calculate tool usage metrics.
        
        Args:
            entries: List of parsed log entries to analyze
            
        Returns:
            Dictionary with 'tool_usage' mapping tool names to counts
        """
        tool_usage: Dict[str, int] = {}
        
        for entry in entries:
            # Look for tool invocations
            if entry.event_type == 'tool_invocation':
                tool_name = entry.data.get('tool_name') or entry.data.get('tool')
                if tool_name:
                    tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1
            
            # Also check for tool information in other event types
            elif 'tool' in entry.data:
                tool_name = entry.data['tool']
                if tool_name:
                    tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1
        
        return {
            'tool_usage': tool_usage
        }
