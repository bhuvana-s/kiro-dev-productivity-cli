"""Integration tests for project extraction from real Kiro logs."""

import pytest
from pathlib import Path
from collections import Counter

from kiro_analyzer.parsers import ParserService
from kiro_analyzer.utils import ProjectExtractor
from kiro_analyzer.analyzers import ProjectMetricsCalculator


# Path to real Kiro application folder
KIRO_APP_FOLDER = Path("/Users/bsubramani/Library/Application Support/Kiro")


@pytest.mark.skipif(not KIRO_APP_FOLDER.exists(), reason="Kiro application folder not found")
class TestProjectExtractionWithRealData:
    """Test project extraction using actual Kiro log files."""
    
    def test_extract_projects_from_real_logs(self):
        """Test extracting project information from real Kiro logs."""
        # Find a recent Kiro log
        log_dirs = list(KIRO_APP_FOLDER.glob("logs/*/window*/exthost/kiro.kiroAgent"))
        if not log_dirs:
            pytest.skip("No Kiro agent log directories found")
        
        log_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        recent_dir = log_dirs[0]
        
        kiro_log = recent_dir / "Kiro Logs.log"
        if not kiro_log.exists():
            pytest.skip("Kiro Logs.log not found")
        
        print(f"\n✓ Analyzing projects in: {kiro_log}")
        
        # Parse the log file
        service = ParserService()
        entries = service.parse_file(kiro_log)
        
        print(f"✓ Parsed {len(entries)} log entries")
        
        # Extract projects from entries
        projects = []
        project_counts = Counter()
        
        for entry in entries:
            project = ProjectExtractor.extract_project_name(entry)
            if project:
                projects.append(project)
                project_counts[project] += 1
        
        # Show results
        unique_projects = set(projects)
        print(f"\n✓ Found {len(unique_projects)} unique projects:")
        
        for project, count in project_counts.most_common(10):
            print(f"  - {project}: {count} entries")
        
        # Show sample log entries with project info
        print("\n✓ Sample log entries with project data:")
        entries_with_project_data = [
            e for e in entries 
            if any(key in e.data for key in ['workspace_path', 'project_name', 'working_directory', 'cwd', 'context'])
        ]
        
        print(f"  Found {len(entries_with_project_data)} entries with project-related fields")
        
        if entries_with_project_data:
            for entry in entries_with_project_data[:3]:  # Show first 3
                print(f"\n  Event: {entry.event_type}")
                for key in ['workspace_path', 'project_name', 'working_directory', 'cwd']:
                    if key in entry.data:
                        print(f"    {key}: {entry.data[key]}")
                if 'context' in entry.data and isinstance(entry.data['context'], dict):
                    if 'workspace' in entry.data['context']:
                        print(f"    context.workspace: {entry.data['context']['workspace']}")
        
        # If no projects found, show what fields ARE available
        if not projects:
            print("\n⚠ No projects extracted. Analyzing available fields:")
            all_fields = Counter()
            for entry in entries[:100]:  # Sample first 100
                all_fields.update(entry.data.keys())
            
            print("\nMost common fields in log entries:")
            for field, count in all_fields.most_common(20):
                print(f"  - {field}: {count}")
    
    def test_project_metrics_with_real_logs(self):
        """Test calculating project-level metrics from real logs."""
        # Find a recent Kiro log
        log_dirs = list(KIRO_APP_FOLDER.glob("logs/*/window*/exthost/kiro.kiroAgent"))
        if not log_dirs:
            pytest.skip("No Kiro agent log directories found")
        
        log_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        recent_dir = log_dirs[0]
        
        kiro_log = recent_dir / "Kiro Logs.log"
        if not kiro_log.exists():
            pytest.skip("Kiro Logs.log not found")
        
        print(f"\n✓ Calculating project metrics from: {kiro_log}")
        
        # Parse the log file
        service = ParserService()
        entries = service.parse_file(kiro_log)
        
        # Calculate project metrics
        calculator = ProjectMetricsCalculator()
        result = calculator.calculate(entries)
        
        print(f"\n✓ Found {len(result['projects'])} projects:")
        for project in result['projects']:
            print(f"  - {project}")
        
        print("\n✓ Project Summary:")
        for project, summary in result['project_summary'].items():
            print(f"\n  {project}:")
            print(f"    Total entries: {summary['total_entries']}")
            print(f"    Total requests: {summary['total_requests']}")
            print(f"    Lines of code: {summary['lines_of_code']}")
        
        # Show detailed metrics for first project
        if result['projects']:
            first_project = result['projects'][0]
            metrics = result['project_metrics'][first_project]
            
            print(f"\n✓ Detailed metrics for '{first_project}':")
            print(f"    Conversations: {metrics.get('total_conversations', 0)}")
            print(f"    Tool usage: {len(metrics.get('tool_usage', {}))}")
            print(f"    Daily breakdown: {len(metrics.get('daily_breakdown', {}))}")
        
        assert len(result['projects']) > 0, "Should find at least one project"
