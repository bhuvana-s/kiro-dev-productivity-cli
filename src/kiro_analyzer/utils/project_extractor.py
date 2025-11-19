"""Utility for extracting project information from log entries."""

from pathlib import Path
from typing import Optional

from ..models import LogEntry


class ProjectExtractor:
    """Extract project/workspace information from log entries.
    
    This utility identifies which project or workspace a log entry belongs to
    by examining workspace paths, project names, or other identifying information
    in the log data.
    """
    
    @staticmethod
    def extract_project_name(entry: LogEntry) -> Optional[str]:
        """Extract project name from a log entry.
        
        Looks for project identifiers in various fields:
        - workspace_path
        - project_name
        - working_directory
        - cwd (current working directory)
        
        Args:
            entry: Log entry to extract project from
            
        Returns:
            Project name/identifier or None if not found
        """
        # Check for explicit project name
        if 'project_name' in entry.data:
            return str(entry.data['project_name'])
        
        # Check for workspace path
        if 'workspace_path' in entry.data:
            workspace_path = entry.data['workspace_path']
            return ProjectExtractor._extract_from_path(workspace_path)
        
        # Check for working directory
        if 'working_directory' in entry.data:
            working_dir = entry.data['working_directory']
            return ProjectExtractor._extract_from_path(working_dir)
        
        # Check for cwd
        if 'cwd' in entry.data:
            cwd = entry.data['cwd']
            return ProjectExtractor._extract_from_path(cwd)
        
        # Check for workspace in nested context
        if 'context' in entry.data and isinstance(entry.data['context'], dict):
            context = entry.data['context']
            if 'workspace' in context:
                return ProjectExtractor._extract_from_path(context['workspace'])
            if 'project' in context:
                return str(context['project'])
        
        return None
    
    @staticmethod
    def _extract_from_path(path_str: str) -> str:
        """Extract project name from a file path.
        
        Takes the last directory name in the path as the project identifier.
        
        Args:
            path_str: File path string
            
        Returns:
            Project name extracted from path
        """
        if not path_str:
            return 'unknown'
        
        try:
            path = Path(path_str)
            # Get the last directory name (project root)
            if path.is_absolute():
                # Find the meaningful project directory
                # Skip common parent directories like 'Documents', 'Projects', etc.
                parts = path.parts
                skip_dirs = {'Users', 'home', 'Documents', 'Projects', 'Code', 'src', 'workspace'}
                
                # Work backwards to find a meaningful directory name
                for part in reversed(parts):
                    if part and part not in skip_dirs and not part.startswith('.'):
                        return part
            
            # Fallback to the name of the path
            return path.name if path.name else 'unknown'
        except Exception:
            return 'unknown'
