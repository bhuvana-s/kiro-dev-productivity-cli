"""Parser registry for managing log parsers."""

from pathlib import Path
from typing import Dict, List, Optional

from ..protocols import LogParser


class ParserRegistry:
    """Registry for managing and selecting log parsers.
    
    The registry maintains a collection of parsers and selects the appropriate
    parser for a given file based on the parser's can_parse() method.
    """
    
    def __init__(self):
        """Initialize an empty parser registry."""
        self._parsers: List[LogParser] = []
    
    def register_parser(self, parser: LogParser) -> None:
        """Register a new parser with the registry.
        
        Args:
            parser: LogParser instance to register
        """
        self._parsers.append(parser)
    
    def get_parser(self, file_path: Path) -> Optional[LogParser]:
        """Get the first parser that can handle the given file.
        
        Args:
            file_path: Path to the log file
            
        Returns:
            LogParser instance that can parse the file, or None if no parser found
        """
        for parser in self._parsers:
            if parser.can_parse(file_path):
                return parser
        return None
    
    def get_all_parsers(self) -> List[LogParser]:
        """Get all registered parsers.
        
        Returns:
            List of all registered LogParser instances
        """
        return self._parsers.copy()
