"""Unit tests for project-level metrics."""

from datetime import datetime
from pathlib import Path

import pytest

from kiro_analyzer.analyzers import ProjectMetricsCalculator
from kiro_analyzer.models import LogEntry
from kiro_analyzer.utils import ProjectExtractor


class TestProjectExtractor:
    """Tests for ProjectExtractor."""
    
    def test_extract_from_project_name(self):
        """Test extracting project from explicit project_name field."""
        entry = LogEntry(
            timestamp=datetime.now(),
            event_type='request',
            data={'project_name': 'my-awesome-project'},
            raw_line='',
            source_file=Path('test.log')
        )
        
        project = ProjectExtractor.extract_project_name(entry)
        assert project == 'my-awesome-project'
    
    def test_extract_from_workspace_path(self):
        """Test extracting project from workspace_path."""
        entry = LogEntry(
            timestamp=datetime.now(),
            event_type='request',
            data={'workspace_path': '/Users/dev/Projects/kiro-analyzer'},
            raw_line='',
            source_file=Path('test.log')
        )
        
        project = ProjectExtractor.extract_project_name(entry)
        assert project == 'kiro-analyzer'
    
    def test_extract_from_working_directory(self):
        """Test extracting project from working_directory."""
        entry = LogEntry(
            timestamp=datetime.now(),
            event_type='request',
            data={'working_directory': '/home/user/code/my-project'},
            raw_line='',
            source_file=Path('test.log')
        )
        
        project = ProjectExtractor.extract_project_name(entry)
        assert project == 'my-project'
    
    def test_extract_from_context(self):
        """Test extracting project from nested context."""
        entry = LogEntry(
            timestamp=datetime.now(),
            event_type='request',
            data={'context': {'workspace': '/Users/dev/awesome-app'}},
            raw_line='',
            source_file=Path('test.log')
        )
        
        project = ProjectExtractor.extract_project_name(entry)
        assert project == 'awesome-app'
    
    def test_no_project_info(self):
        """Test handling entries without project information."""
        entry = LogEntry(
            timestamp=datetime.now(),
            event_type='request',
            data={},
            raw_line='',
            source_file=Path('test.log')
        )
        
        project = ProjectExtractor.extract_project_name(entry)
        assert project is None


class TestProjectMetricsCalculator:
    """Tests for ProjectMetricsCalculator."""
    
    def test_group_entries_by_project(self):
        """Test grouping log entries by project."""
        entries = [
            LogEntry(
                timestamp=datetime.now(),
                event_type='request',
                data={'project_name': 'project-a'},
                raw_line='',
                source_file=Path('test.log')
            ),
            LogEntry(
                timestamp=datetime.now(),
                event_type='request',
                data={'project_name': 'project-a'},
                raw_line='',
                source_file=Path('test.log')
            ),
            LogEntry(
                timestamp=datetime.now(),
                event_type='request',
                data={'project_name': 'project-b'},
                raw_line='',
                source_file=Path('test.log')
            ),
        ]
        
        calculator = ProjectMetricsCalculator()
        result = calculator.calculate(entries)
        
        assert 'project-a' in result['projects']
        assert 'project-b' in result['projects']
        assert len(result['projects']) == 2
    
    def test_calculate_per_project_metrics(self):
        """Test calculating metrics for each project."""
        entries = [
            LogEntry(
                timestamp=datetime.now(),
                event_type='request',
                data={'project_name': 'project-a'},
                raw_line='',
                source_file=Path('test.log')
            ),
            LogEntry(
                timestamp=datetime.now(),
                event_type='request',
                data={'project_name': 'project-a'},
                raw_line='',
                source_file=Path('test.log')
            ),
            LogEntry(
                timestamp=datetime.now(),
                event_type='request',
                data={'project_name': 'project-b'},
                raw_line='',
                source_file=Path('test.log')
            ),
        ]
        
        calculator = ProjectMetricsCalculator()
        result = calculator.calculate(entries)
        
        # Check project-a metrics
        assert result['project_metrics']['project-a']['total_requests'] == 2
        
        # Check project-b metrics
        assert result['project_metrics']['project-b']['total_requests'] == 1
    
    def test_project_summary(self):
        """Test project summary generation."""
        entries = [
            LogEntry(
                timestamp=datetime.now(),
                event_type='request',
                data={
                    'project_name': 'project-a',
                    'lines_generated': 50,
                    'language': 'python'
                },
                raw_line='',
                source_file=Path('test.log')
            ),
        ]
        
        calculator = ProjectMetricsCalculator()
        result = calculator.calculate(entries)
        
        summary = result['project_summary']['project-a']
        assert summary['total_entries'] == 1
        assert summary['total_requests'] == 1
        assert summary['lines_of_code'] == 50
    
    def test_unknown_project_handling(self):
        """Test handling entries without project information."""
        entries = [
            LogEntry(
                timestamp=datetime.now(),
                event_type='request',
                data={},  # No project info
                raw_line='',
                source_file=Path('test.log')
            ),
        ]
        
        calculator = ProjectMetricsCalculator()
        result = calculator.calculate(entries)
        
        assert 'unknown' in result['projects']
        assert result['project_metrics']['unknown']['total_requests'] == 1
