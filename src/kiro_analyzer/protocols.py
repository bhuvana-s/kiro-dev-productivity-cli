"""Protocol interfaces for extensibility in Kiro Activity Analyzer."""

from pathlib import Path
from typing import Any, Dict, Iterator, List, Protocol

from .models import LogEntry, ProductivityMetrics


class LogParser(Protocol):
    """Protocol for log file parsers.
    
    Implementations should be able to determine if they can parse a file
    and then parse it into structured LogEntry objects.
    """
    
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file.
        
        Args:
            file_path: Path to the log file to check
            
        Returns:
            True if this parser can parse the file, False otherwise
        """
        ...
    
    def parse(self, file_path: Path) -> Iterator[LogEntry]:
        """Parse a log file and yield log entries.
        
        Args:
            file_path: Path to the log file to parse
            
        Yields:
            LogEntry objects parsed from the file
            
        Raises:
            LogParsingError: If the file cannot be parsed
        """
        ...


class MetricCalculator(Protocol):
    """Protocol for metric calculators.
    
    Implementations should calculate specific metrics from log entries.
    """
    
    def calculate(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """Calculate metrics from log entries.
        
        Args:
            entries: List of parsed log entries to analyze
            
        Returns:
            Dictionary containing calculated metric values
        """
        ...


class CLICommand(Protocol):
    """Protocol for CLI command implementations.
    
    Implementations should execute a specific command and return an exit code.
    """
    
    def execute(self, args: Dict[str, Any]) -> int:
        """Execute the command with given arguments.
        
        Args:
            args: Dictionary of command arguments and options
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        ...


class OutputFormatter(Protocol):
    """Protocol for output formatting.
    
    Implementations should format metrics and data for display or export.
    """
    
    def format_metrics(self, metrics: ProductivityMetrics) -> str:
        """Format productivity metrics for output.
        
        Args:
            metrics: ProductivityMetrics object to format
            
        Returns:
            Formatted string representation of the metrics
        """
        ...
    
    def format_table(self, data: List[Dict[str, Any]]) -> str:
        """Format tabular data for output.
        
        Args:
            data: List of dictionaries representing table rows
            
        Returns:
            Formatted string representation of the table
        """
        ...
