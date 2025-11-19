"""Unit tests for Kiro-specific parsers."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from kiro_analyzer.parsers import KiroLogParser, MarkdownParser


class TestKiroLogParser:
    """Tests for KiroLogParser."""
    
    def test_can_parse_kiro_log_file(self, tmp_path):
        """Test that parser recognizes Kiro log files."""
        parser = KiroLogParser()
        
        # Create a file in a Kiro-like path
        kiro_path = tmp_path / "kiro.kiroAgent"
        kiro_path.mkdir()
        log_file = kiro_path / "Kiro Logs.log"
        log_file.write_text("2025-11-19 23:03:58.159 [info] Test log")
        
        assert parser.can_parse(log_file)
    
    def test_parse_kiro_log_entry(self, tmp_path):
        """Test parsing a Kiro log entry."""
        parser = KiroLogParser()
        log_file = tmp_path / "kiro.kiroAgent" / "test.log"
        log_file.parent.mkdir(parents=True)
        
        log_content = """2025-11-19 23:03:58.159 [info] [agent-controller] Triggered new agent: spec-generation (autonomyMode=Supervised)
2025-11-19 23:03:59.598 [info] Congratulations, "Kiro" is now active!"""
        
        log_file.write_text(log_content)
        
        entries = list(parser.parse(log_file))
        assert len(entries) == 2
        assert entries[0].event_type == 'conversation_start'
        assert entries[0].data.get('autonomy_mode') == 'Supervised'
    
    def test_extract_tool_usage(self, tmp_path):
        """Test extracting tool usage from Kiro logs."""
        parser = KiroLogParser()
        log_file = tmp_path / "kiro.kiroAgent" / "test.log"
        log_file.parent.mkdir(parents=True)
        
        log_content = '2025-11-19 23:08:09.520 [info] [Tool agent Action] setup node'
        log_file.write_text(log_content)
        
        entries = list(parser.parse(log_file))
        assert len(entries) == 1
        assert entries[0].event_type == 'tool_invocation'
        assert entries[0].data.get('tool_invocation') is True


class TestMarkdownParser:
    """Tests for MarkdownParser."""
    
    def test_can_parse_markdown_file(self, tmp_path):
        """Test that parser recognizes markdown files in Kiro storage."""
        parser = MarkdownParser()
        
        # Create a file in a Kiro-like path
        kiro_path = tmp_path / "Library" / "Application Support" / "Kiro" / "User"
        kiro_path.mkdir(parents=True)
        md_file = kiro_path / "README.md"
        md_file.write_text("# Test Project")
        
        assert parser.can_parse(md_file)
    
    def test_parse_markdown_content(self, tmp_path):
        """Test parsing markdown content."""
        parser = MarkdownParser()
        kiro_path = tmp_path / "Library" / "Application Support" / "Kiro" / "User"
        kiro_path.mkdir(parents=True)
        md_file = kiro_path / "README.md"
        
        content = """# Test Project

## Features

- Feature 1
- Feature 2

## Code Example

```python
def hello():
    print("Hello, World!")
```

[Link](https://example.com)
"""
        md_file.write_text(content)
        
        entries = list(parser.parse(md_file))
        assert len(entries) == 1
        
        entry = entries[0]
        assert entry.event_type == 'project_documentation'
        assert entry.data['project_title'] == 'Test Project'
        assert entry.data['heading_count'] == 3
        assert entry.data['bullet_count'] == 2
        assert entry.data['code_block_count'] == 1
        assert 'python' in entry.data['languages']
        assert entry.data['link_count'] == 1
    
    def test_identify_project_type(self, tmp_path):
        """Test project type identification."""
        parser = MarkdownParser()
        kiro_path = tmp_path / "Library" / "Application Support" / "Kiro" / "User"
        kiro_path.mkdir(parents=True)
        md_file = kiro_path / "README.md"
        
        content = """# React Frontend App

Built with React and TypeScript for modern web development.
"""
        md_file.write_text(content)
        
        entries = list(parser.parse(md_file))
        assert len(entries) == 1
        assert entries[0].data['project_type'] == 'frontend'
