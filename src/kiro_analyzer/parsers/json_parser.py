"""JSON log file parser."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Iterator

from ..models import LogEntry
from .base import stream_file_lines

logger = logging.getLogger(__name__)


class JSONLogParser:
    """Parser for JSON-formatted log files.
    
    This parser handles log files where each line is a valid JSON object.
    It extracts timestamp, event_type, and data fields from each entry.
    """
    
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file.
        
        Args:
            file_path: Path to the log file to check
            
        Returns:
            True if file has .json extension or .log extension with JSON content
        """
        # Check file extension
        if file_path.suffix.lower() in ['.json', '.jsonl']:
            return True
        
        # For .log files, try to peek at first line to see if it's JSON
        if file_path.suffix.lower() == '.log':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if first_line:
                        json.loads(first_line)
                        return True
            except (json.JSONDecodeError, IOError):
                pass
        
        return False
    
    def parse(self, file_path: Path) -> Iterator[LogEntry]:
        """Parse a JSON log file and yield log entries.
        
        Each line in the file should be a valid JSON object with at least
        a timestamp field. The parser handles malformed entries gracefully
        by logging warnings and continuing with the next line.
        
        Args:
            file_path: Path to the log file to parse
            
        Yields:
            LogEntry objects parsed from the file
        """
        line_number = 0
        
        for line in stream_file_lines(file_path):
            line_number += 1
            
            # Skip empty lines
            if not line.strip():
                continue
            
            try:
                # Parse JSON
                data = json.loads(line)
                
                # Extract timestamp
                timestamp = self._extract_timestamp(data, line_number)
                if timestamp is None:
                    continue
                
                # Extract event type
                event_type = self._extract_event_type(data)
                
                # Create log entry
                yield LogEntry(
                    timestamp=timestamp,
                    event_type=event_type,
                    data=data,
                    raw_line=line,
                    source_file=file_path
                )
                
            except json.JSONDecodeError as e:
                logger.warning(
                    f"Malformed JSON at {file_path}:{line_number}: {e}. Skipping line."
                )
                continue
            except Exception as e:
                logger.warning(
                    f"Error parsing line {line_number} in {file_path}: {e}. Skipping line."
                )
                continue
    
    def _extract_timestamp(self, data: dict, line_number: int) -> datetime | None:
        """Extract timestamp from JSON data.
        
        Args:
            data: Parsed JSON data
            line_number: Line number for error reporting
            
        Returns:
            Parsed datetime object or None if timestamp cannot be extracted
        """
        # Try common timestamp field names
        timestamp_fields = ['timestamp', 'time', 'datetime', 'date', '@timestamp', 'ts']
        
        for field in timestamp_fields:
            if field in data:
                timestamp_value = data[field]
                try:
                    # Try parsing ISO format
                    if isinstance(timestamp_value, str):
                        return datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
                    # Try parsing Unix timestamp (seconds or milliseconds)
                    elif isinstance(timestamp_value, (int, float)):
                        # If value is very large, assume milliseconds
                        if timestamp_value > 1e10:
                            return datetime.fromtimestamp(timestamp_value / 1000)
                        else:
                            return datetime.fromtimestamp(timestamp_value)
                except (ValueError, OSError) as e:
                    logger.warning(f"Invalid timestamp format at line {line_number}: {e}")
                    continue
        
        logger.warning(f"No valid timestamp found at line {line_number}")
        return None
    
    def _extract_event_type(self, data: dict) -> str:
        """Extract event type from JSON data.
        
        Args:
            data: Parsed JSON data
            
        Returns:
            Event type string, defaults to 'unknown' if not found
        """
        # Try common event type field names
        event_fields = ['event_type', 'event', 'type', 'level', 'action']
        
        for field in event_fields:
            if field in data:
                return str(data[field])
        
        return 'unknown'
