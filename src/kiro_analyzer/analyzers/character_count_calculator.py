"""Calculator for character processing metrics."""

from typing import Any, Dict, List

from ..models import LogEntry


class CharacterCountCalculator:
    """Calculate total characters processed from log entries.
    
    This calculator implements the MetricCalculator protocol to sum:
    - Total characters processed across all requests
    """
    
    def calculate(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """Calculate total characters processed.
        
        Args:
            entries: List of parsed log entries to analyze
            
        Returns:
            Dictionary with 'total_characters_processed'
        """
        total_characters = 0
        
        for entry in entries:
            # Look for character count in various fields
            if 'character_count' in entry.data:
                try:
                    count = int(entry.data['character_count'])
                    if count > 0:
                        total_characters += count
                except (ValueError, TypeError):
                    pass
            elif 'characters' in entry.data:
                try:
                    count = int(entry.data['characters'])
                    if count > 0:
                        total_characters += count
                except (ValueError, TypeError):
                    pass
            elif 'chars_processed' in entry.data:
                try:
                    count = int(entry.data['chars_processed'])
                    if count > 0:
                        total_characters += count
                except (ValueError, TypeError):
                    pass
            # Also check if there's request content we can count
            elif 'content' in entry.data and isinstance(entry.data['content'], str):
                total_characters += len(entry.data['content'])
            elif 'request' in entry.data and isinstance(entry.data['request'], str):
                total_characters += len(entry.data['request'])
        
        return {
            'total_characters_processed': total_characters
        }
