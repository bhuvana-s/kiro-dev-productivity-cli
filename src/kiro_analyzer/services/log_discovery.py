"""Log discovery service for finding and cataloging Kiro log files."""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..models import LogFileMetadata


class LogDiscoveryService:
    """Service for discovering and cataloging log files in the Kiro application folder.
    
    This service scans the Kiro application directory recursively to find log files,
    extracts metadata, and filters them based on various criteria like date ranges.
    """
    
    # Recognized log file patterns and their descriptions
    LOG_PATTERNS = {
        "*.log": "Plain text log files",
        "*.json": "JSON-formatted log files",
        "*activity*.log": "Activity tracking logs",
        "*activity*.json": "Activity tracking logs (JSON format)",
        "*metrics*.log": "Metrics and performance logs",
        "*metrics*.json": "Metrics and performance logs (JSON format)",
        "*session*.log": "Session information logs",
        "*session*.json": "Session information logs (JSON format)",
    }
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize the log discovery service.
        
        Args:
            base_path: Base directory to search for logs. If None, uses default Kiro folder.
        """
        self.base_path = base_path
    
    def discover_logs(
        self,
        base_path: Optional[Path] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[LogFileMetadata]:
        """Discover log files within the specified directory and date range.
        
        Scans the base directory recursively for log files matching recognized patterns,
        extracts file metadata, and filters by modification time if date range is provided.
        
        Args:
            base_path: Directory to search. If None, uses instance base_path.
            start_date: Optional start date for filtering (inclusive)
            end_date: Optional end date for filtering (inclusive)
            
        Returns:
            List of LogFileMetadata objects for discovered files
            
        Raises:
            FileNotFoundError: If the base_path does not exist
            PermissionError: If the base_path is not accessible
        """
        search_path = base_path or self.base_path
        
        if search_path is None:
            raise ValueError("No base path specified for log discovery")
        
        if not search_path.exists():
            raise FileNotFoundError(f"Log directory does not exist: {search_path}")
        
        if not os.access(search_path, os.R_OK):
            raise PermissionError(f"Cannot read log directory: {search_path}")
        
        discovered_files: List[LogFileMetadata] = []
        
        # Recursively walk through the directory
        for root, _, files in os.walk(search_path):
            root_path = Path(root)
            
            for filename in files:
                file_path = root_path / filename
                
                # Check if file matches recognized patterns
                if self._matches_log_pattern(file_path):
                    try:
                        metadata = self._extract_metadata(file_path)
                        
                        # Filter by date range if specified
                        if self._is_within_date_range(metadata, start_date, end_date):
                            discovered_files.append(metadata)
                    except (OSError, PermissionError):
                        # Skip files we can't access
                        continue
        
        return discovered_files
    
    def get_log_patterns(self) -> Dict[str, str]:
        """Return dictionary of recognized log file patterns and descriptions.
        
        Returns:
            Dictionary mapping file patterns to their descriptions
        """
        return self.LOG_PATTERNS.copy()
    
    def _matches_log_pattern(self, file_path: Path) -> bool:
        """Check if a file matches any recognized log pattern.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file matches a log pattern, False otherwise
        """
        filename = file_path.name.lower()
        
        # Check for .log or .json extensions
        if not (filename.endswith('.log') or filename.endswith('.json')):
            return False
        
        return True
    
    def _extract_metadata(self, file_path: Path) -> LogFileMetadata:
        """Extract metadata from a log file.
        
        Args:
            file_path: Path to the log file
            
        Returns:
            LogFileMetadata object with file information
            
        Raises:
            OSError: If file stats cannot be retrieved
        """
        stat_info = file_path.stat()
        
        # Determine file type based on filename patterns
        file_type = self._determine_file_type(file_path)
        
        return LogFileMetadata(
            path=file_path,
            file_type=file_type,
            size_bytes=stat_info.st_size,
            created_at=datetime.fromtimestamp(stat_info.st_ctime),
            modified_at=datetime.fromtimestamp(stat_info.st_mtime)
        )
    
    def _determine_file_type(self, file_path: Path) -> str:
        """Determine the type of log file based on its name.
        
        Args:
            file_path: Path to the log file
            
        Returns:
            String indicating file type ('activity', 'metrics', 'session', or 'general')
        """
        filename_lower = file_path.name.lower()
        
        if 'activity' in filename_lower:
            return 'activity'
        elif 'metrics' in filename_lower:
            return 'metrics'
        elif 'session' in filename_lower:
            return 'session'
        else:
            return 'general'
    
    def _is_within_date_range(
        self,
        metadata: LogFileMetadata,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> bool:
        """Check if a file's modification time is within the specified date range.
        
        Args:
            metadata: LogFileMetadata to check
            start_date: Optional start date (inclusive)
            end_date: Optional end date (inclusive)
            
        Returns:
            True if the file is within the date range (or no range specified)
        """
        if start_date is None and end_date is None:
            return True
        
        mod_time = metadata.modified_at
        
        if start_date is not None and mod_time < start_date:
            return False
        
        if end_date is not None and mod_time > end_date:
            return False
        
        return True
