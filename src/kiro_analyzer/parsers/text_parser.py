"""Plain text log file parser."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional, Pattern

from ..models import LogEntry
from .base import stream_file_lines

logger = logging.getLogger(__name__)


class PlainTextLogParser:
    """Parser for plain text structured log files.
    
    This parser uses regex patterns to extract structured information from
    plain text log files. It supports common log formats with timestamps
    and event information.
    """
    
    # Common log format patterns
    # Format: [timestamp] [level/event] message
    PATTERN_BRACKETED = re.compile(
        r'^\[(?P<timestamp>[^\]]+)\]\s*\[(?P<event_type>[^\]]+)\]\s*(?P<message>.*)'
    )
    
    # Format: timestamp level: message
    PATTERN_COLON = re.compile(
        r'^(?P<timestamp>\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)\s+(?P<event_type>\w+):\s*(?P<message>.*)'
    )
    
    # Format: timestamp - level - message
    PATTERN_DASH = re.compile(
        r'^(?P<timestamp>\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)\s+-\s+(?P<event_type>\w+)\s+-\s+(?P<message>.*)'
    )
    
    def __init__(self):
        """Initialize the plain text parser with default patterns."""
        self.patterns = [
            self.PATTERN_BRACKETED,
            self.PATTERN_COLON,
            self.PATTERN_DASH
        ]
    
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file.
        
        Args:
            file_path: Path to the log file to check
            
        Returns:
            True if file has .log or .txt extension
        """
        return file_path.suffix.lower() in ['.log', '.txt']
    
    def parse(self, file_path: Path) -> Iterator[LogEntry]:
        """Parse a plain text log file and yield log entries.
        
        The parser tries multiple regex patterns to extract structured data.
        Lines that don't match any pattern are skipped with a warning.
        
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
            
            # Try each pattern
            for pattern in self.patterns:
                match = pattern.match(line)
                if match:
                    try:
                        groups = match.groupdict()
                        
                        # Extract timestamp
                        timestamp = self._parse_timestamp(groups.get('timestamp', ''))
                        if timestamp is None:
                            logger.warning(
                                f"Could not parse timestamp at {file_path}:{line_number}"
                            )
                            break
                        
                        # Extract event type
                        event_type = groups.get('event_type', 'unknown').strip()
                        
                        # Extract message and any additional data
                        message = groups.get('message', '').strip()
                        data = {
                            'message': message,
                            'event_type': event_type
                        }
                        
                        # Create log entry
                        yield LogEntry(
                            timestamp=timestamp,
                            event_type=event_type,
                            data=data,
                            raw_line=line,
                            source_file=file_path
                        )
                        break
                        
                    except Exception as e:
                        logger.warning(
                            f"Error parsing line {line_number} in {file_path}: {e}"
                        )
                        break
            else:
                # No pattern matched
                logger.debug(
                    f"No pattern matched for line {line_number} in {file_path}"
                )
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string into datetime object.
        
        Args:
            timestamp_str: Timestamp string to parse
            
        Returns:
            Parsed datetime object or None if parsing fails
        """
        if not timestamp_str:
            return None
        
        # Try ISO format first
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except ValueError:
            pass
        
        # Try common formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%d/%b/%Y:%H:%M:%S',
            '%Y/%m/%d %H:%M:%S',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def add_pattern(self, pattern: Pattern) -> None:
        """Add a custom regex pattern for parsing.
        
        Args:
            pattern: Compiled regex pattern with named groups for
                    'timestamp', 'event_type', and optionally 'message'
        """
        self.patterns.append(pattern)
