"""Parser service for orchestrating log file parsing."""

import logging
from pathlib import Path
from typing import List

from ..models import LogEntry
from .registry import ParserRegistry
from .json_parser import JSONLogParser
from .text_parser import PlainTextLogParser

logger = logging.getLogger(__name__)


class ParserService:
    """Service for parsing log files using registered parsers.
    
    The ParserService orchestrates the parsing process by selecting the
    appropriate parser for each file and handling errors gracefully.
    """
    
    def __init__(self, registry: ParserRegistry = None):
        """Initialize the parser service.
        
        Args:
            registry: ParserRegistry instance. If None, creates a new registry
                     with default parsers (JSONLogParser and PlainTextLogParser)
        """
        if registry is None:
            registry = ParserRegistry()
            # Register default parsers
            registry.register_parser(JSONLogParser())
            registry.register_parser(PlainTextLogParser())
        
        self.registry = registry
    
    def parse_file(self, file_path: Path) -> List[LogEntry]:
        """Parse a log file and return successfully parsed entries.
        
        This method selects the appropriate parser for the file, parses it,
        and handles any errors that occur during parsing. Parsing errors for
        individual entries are logged but don't stop the parsing process.
        
        Args:
            file_path: Path to the log file to parse
            
        Returns:
            List of successfully parsed LogEntry objects
            
        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If no parser can handle the file
        """
        # Check if file exists
        if not file_path.exists():
            raise FileNotFoundError(f"Log file not found: {file_path}")
        
        # Get appropriate parser
        parser = self.registry.get_parser(file_path)
        if parser is None:
            raise ValueError(f"No parser available for file: {file_path}")
        
        logger.info(f"Parsing {file_path} with {parser.__class__.__name__}")
        
        # Parse file and collect entries
        entries = []
        error_count = 0
        
        try:
            for entry in parser.parse(file_path):
                entries.append(entry)
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            error_count += 1
        
        logger.info(
            f"Parsed {len(entries)} entries from {file_path}"
            + (f" ({error_count} errors)" if error_count > 0 else "")
        )
        
        return entries
    
    def parse_files(self, file_paths: List[Path]) -> List[LogEntry]:
        """Parse multiple log files and return all successfully parsed entries.
        
        This method parses multiple files and aggregates all entries.
        Errors in individual files don't stop the parsing of other files.
        
        Args:
            file_paths: List of paths to log files to parse
            
        Returns:
            List of all successfully parsed LogEntry objects from all files
        """
        all_entries = []
        
        for file_path in file_paths:
            try:
                entries = self.parse_file(file_path)
                all_entries.extend(entries)
            except (FileNotFoundError, ValueError) as e:
                logger.warning(f"Skipping {file_path}: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error parsing {file_path}: {e}")
                continue
        
        logger.info(f"Parsed {len(all_entries)} total entries from {len(file_paths)} files")
        
        return all_entries
