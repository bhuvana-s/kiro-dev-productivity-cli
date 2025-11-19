"""Calculator for project-level metrics."""

from collections import defaultdict
from typing import Any, Dict, List

from ..models import LogEntry
from ..utils import ProjectExtractor
from .activity_pattern_calculator import ActivityPatternCalculator
from .character_count_calculator import CharacterCountCalculator
from .code_generation_calculator import CodeGenerationCalculator
from .model_usage_calculator import ModelUsageCalculator
from .request_count_calculator import RequestCountCalculator
from .response_time_calculator import ResponseTimeCalculator
from .tool_usage_calculator import ToolUsageCalculator


class ProjectMetricsCalculator:
    """Calculate metrics grouped by project.
    
    This calculator groups log entries by project and computes
    all standard metrics for each project separately.
    """
    
    def __init__(self):
        """Initialize with all standard calculators."""
        self.request_calculator = RequestCountCalculator()
        self.response_calculator = ResponseTimeCalculator()
        self.code_calculator = CodeGenerationCalculator()
        self.tool_calculator = ToolUsageCalculator()
        self.activity_calculator = ActivityPatternCalculator()
        self.character_calculator = CharacterCountCalculator()
        self.model_calculator = ModelUsageCalculator()
    
    def calculate(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """Calculate metrics grouped by project.
        
        Args:
            entries: List of parsed log entries to analyze
            
        Returns:
            Dictionary with:
            - 'projects': List of project names
            - 'project_metrics': Dict mapping project names to their metrics
            - 'project_summary': Dict with project activity counts
        """
        # Group entries by project
        entries_by_project = self._group_by_project(entries)
        
        # Calculate metrics for each project
        project_metrics = {}
        project_summary = {}
        
        for project_name, project_entries in entries_by_project.items():
            metrics = self._calculate_project_metrics(project_entries)
            project_metrics[project_name] = metrics
            project_summary[project_name] = {
                'total_entries': len(project_entries),
                'total_requests': metrics.get('total_requests', 0),
                'lines_of_code': metrics.get('lines_of_code_generated', 0)
            }
        
        return {
            'projects': sorted(entries_by_project.keys()),
            'project_metrics': project_metrics,
            'project_summary': project_summary
        }
    
    def _group_by_project(self, entries: List[LogEntry]) -> Dict[str, List[LogEntry]]:
        """Group log entries by project.
        
        Args:
            entries: List of log entries
            
        Returns:
            Dictionary mapping project names to lists of entries
        """
        grouped: Dict[str, List[LogEntry]] = defaultdict(list)
        
        for entry in entries:
            project_name = ProjectExtractor.extract_project_name(entry)
            if project_name:
                grouped[project_name].append(entry)
            else:
                grouped['unknown'].append(entry)
        
        return dict(grouped)
    
    def _calculate_project_metrics(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """Calculate all metrics for a single project.
        
        Args:
            entries: Log entries for a specific project
            
        Returns:
            Dictionary containing all calculated metrics
        """
        metrics = {}
        
        # Request counts
        metrics.update(self.request_calculator.calculate(entries))
        
        # Response times
        metrics.update(self.response_calculator.calculate(entries))
        
        # Code generation
        metrics.update(self.code_calculator.calculate(entries))
        
        # Tool usage
        metrics.update(self.tool_calculator.calculate(entries))
        
        # Activity patterns
        metrics.update(self.activity_calculator.calculate(entries))
        
        # Character counts
        metrics.update(self.character_calculator.calculate(entries))
        
        # Model usage
        metrics.update(self.model_calculator.calculate(entries))
        
        return metrics
