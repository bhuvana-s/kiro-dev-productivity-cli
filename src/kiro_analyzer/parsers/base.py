"""Base utilities for log parsing."""

from pathlib import Path
from typing import Iterator, Optional


def stream_file_lines(file_path: Path, encoding: str = 'utf-8', chunk_size: int = 8192) -> Iterator[str]:
    """Stream lines from a file efficiently for large files.
    
    This function reads files line-by-line without loading the entire file
    into memory, making it suitable for processing large log files.
    
    Args:
        file_path: Path to the file to read
        encoding: Character encoding of the file (default: utf-8)
        chunk_size: Size of read buffer in bytes (default: 8192)
        
    Yields:
        Individual lines from the file (without newline characters)
        
    Raises:
        IOError: If the file cannot be read
        UnicodeDecodeError: If the file encoding is incorrect
    """
    with open(file_path, 'r', encoding=encoding, buffering=chunk_size) as f:
        for line in f:
            yield line.rstrip('\n\r')


class ParsingUtilities:
    """Common utilities for parsing log files."""
    
    @staticmethod
    def safe_get(data: dict, key: str, default: Optional[any] = None) -> any:
        """Safely get a value from a dictionary with a default.
        
        Args:
            data: Dictionary to get value from
            key: Key to look up
            default: Default value if key not found
            
        Returns:
            Value from dictionary or default
        """
        return data.get(key, default)
    
    @staticmethod
    def is_empty_line(line: str) -> bool:
        """Check if a line is empty or whitespace only.
        
        Args:
            line: Line to check
            
        Returns:
            True if line is empty or whitespace only
        """
        return not line or line.isspace()
