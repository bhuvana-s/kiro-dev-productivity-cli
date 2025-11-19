"""Unit tests for LogDiscoveryService."""

import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from kiro_analyzer.services import LogDiscoveryService
from kiro_analyzer.models import LogFileMetadata


class TestLogDiscoveryService:
    """Test suite for LogDiscoveryService."""
    
    def test_get_log_patterns(self):
        """Test that get_log_patterns returns expected patterns."""
        service = LogDiscoveryService()
        patterns = service.get_log_patterns()
        
        assert isinstance(patterns, dict)
        assert "*.log" in patterns
        assert "*.json" in patterns
        assert "*activity*.log" in patterns
        assert "*metrics*.json" in patterns
    
    def test_discover_logs_with_no_base_path_raises_error(self):
        """Test that discover_logs raises ValueError when no base path is provided."""
        service = LogDiscoveryService()
        
        with pytest.raises(ValueError, match="No base path specified"):
            service.discover_logs()
    
    def test_discover_logs_with_nonexistent_path_raises_error(self):
        """Test that discover_logs raises FileNotFoundError for nonexistent path."""
        service = LogDiscoveryService()
        nonexistent_path = Path("/nonexistent/path/to/logs")
        
        with pytest.raises(FileNotFoundError, match="does not exist"):
            service.discover_logs(base_path=nonexistent_path)
    
    def test_discover_logs_finds_log_files(self):
        """Test that discover_logs finds .log and .json files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create test log files
            (tmp_path / "activity.log").touch()
            (tmp_path / "metrics.json").touch()
            (tmp_path / "session.log").touch()
            (tmp_path / "readme.txt").touch()  # Should be ignored
            
            service = LogDiscoveryService(base_path=tmp_path)
            discovered = service.discover_logs()
            
            assert len(discovered) == 3
            assert all(isinstance(f, LogFileMetadata) for f in discovered)
            
            # Check that only log/json files were found
            filenames = {f.path.name for f in discovered}
            assert "activity.log" in filenames
            assert "metrics.json" in filenames
            assert "session.log" in filenames
            assert "readme.txt" not in filenames
    
    def test_discover_logs_extracts_metadata(self):
        """Test that discover_logs extracts correct file metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.log"
            test_file.write_text("test content")
            
            service = LogDiscoveryService(base_path=tmp_path)
            discovered = service.discover_logs()
            
            assert len(discovered) == 1
            metadata = discovered[0]
            
            assert metadata.path == test_file
            assert metadata.size_bytes > 0
            assert isinstance(metadata.created_at, datetime)
            assert isinstance(metadata.modified_at, datetime)
    
    def test_discover_logs_determines_file_types(self):
        """Test that discover_logs correctly determines file types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create files with different type indicators
            (tmp_path / "activity_log.log").touch()
            (tmp_path / "metrics_data.json").touch()
            (tmp_path / "session_info.log").touch()
            (tmp_path / "general.log").touch()
            
            service = LogDiscoveryService(base_path=tmp_path)
            discovered = service.discover_logs()
            
            file_types = {f.path.name: f.file_type for f in discovered}
            
            assert file_types["activity_log.log"] == "activity"
            assert file_types["metrics_data.json"] == "metrics"
            assert file_types["session_info.log"] == "session"
            assert file_types["general.log"] == "general"
    
    def test_discover_logs_filters_by_date_range(self):
        """Test that discover_logs filters files by modification date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create test files
            old_file = tmp_path / "old.log"
            recent_file = tmp_path / "recent.log"
            old_file.touch()
            recent_file.touch()
            
            # Modify timestamps
            now = datetime.now()
            old_time = (now - timedelta(days=10)).timestamp()
            recent_time = (now - timedelta(days=2)).timestamp()
            
            os.utime(old_file, (old_time, old_time))
            os.utime(recent_file, (recent_time, recent_time))
            
            service = LogDiscoveryService(base_path=tmp_path)
            
            # Filter to last 5 days
            start_date = now - timedelta(days=5)
            discovered = service.discover_logs(start_date=start_date)
            
            assert len(discovered) == 1
            assert discovered[0].path.name == "recent.log"
    
    def test_discover_logs_recursive_search(self):
        """Test that discover_logs searches subdirectories recursively."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create nested directory structure
            subdir = tmp_path / "logs" / "2024"
            subdir.mkdir(parents=True)
            
            (tmp_path / "root.log").touch()
            (subdir / "nested.log").touch()
            
            service = LogDiscoveryService(base_path=tmp_path)
            discovered = service.discover_logs()
            
            assert len(discovered) == 2
            filenames = {f.path.name for f in discovered}
            assert "root.log" in filenames
            assert "nested.log" in filenames
