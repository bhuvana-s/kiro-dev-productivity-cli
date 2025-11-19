"""Markdown file parser for extracting project information."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional, Dict, Any

from ..models import LogEntry
from .base import stream_file_lines

logger = logging.getLogger(__name__)


class MarkdownParser:
    """Parser for markdown files in Kiro workspace storage.
    
    Extracts project information, documentation, and metadata from README
    and other markdown files stored in Kiro's workspace storage.
    """
    
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if file is a markdown file in Kiro storage
        """
        # Check if it's a markdown file
        if file_path.suffix.lower() not in ['.md', '.markdown']:
            return False
        
        # Check if it's in Kiro's storage
        path_str = str(file_path)
        return 'Library/Application Support/Kiro' in path_str
    
    def parse(self, file_path: Path) -> Iterator[LogEntry]:
        """Parse a markdown file and yield a single log entry with extracted data.
        
        Args:
            file_path: Path to the markdown file to parse
            
        Yields:
            Single LogEntry with markdown content and metadata
        """
        try:
            # Read entire file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata
            data = self._extract_markdown_data(content, file_path)
            
            # Use file modification time as timestamp
            timestamp = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            yield LogEntry(
                timestamp=timestamp,
                event_type='project_documentation',
                data=data,
                raw_line=content[:500],  # First 500 chars as preview
                source_file=file_path
            )
            
        except Exception as e:
            logger.warning(f"Error parsing markdown file {file_path}: {e}")
    
    def _extract_markdown_data(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Extract structured data from markdown content.
        
        Args:
            content: Markdown file content
            file_path: Path to the file
            
        Returns:
            Dictionary of extracted data
        """
        data = {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'content_length': len(content),
            'line_count': content.count('\n')
        }
        
        # Extract title (first H1 heading)
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            data['project_title'] = title_match.group(1).strip()
        
        # Extract all headings
        headings = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
        data['heading_count'] = len(headings)
        if headings:
            data['headings'] = headings[:10]  # First 10 headings
        
        # Extract code blocks
        code_blocks = re.findall(r'```(\w*)\n(.*?)```', content, re.DOTALL)
        if code_blocks:
            data['code_block_count'] = len(code_blocks)
            # Count lines of code in blocks
            total_code_lines = sum(block[1].count('\n') for block in code_blocks)
            data['code_lines'] = total_code_lines
            
            # Extract languages used
            languages = [lang for lang, _ in code_blocks if lang]
            if languages:
                data['languages'] = list(set(languages))
        
        # Extract links
        links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', content)
        if links:
            data['link_count'] = len(links)
        
        # Extract features/bullet points
        bullets = re.findall(r'^\s*[-*+]\s+(.+)$', content, re.MULTILINE)
        if bullets:
            data['bullet_count'] = len(bullets)
        
        # Try to identify project type from content
        data['project_type'] = self._identify_project_type(content)
        
        # Extract workspace ID from path
        workspace_match = re.search(r'/([a-f0-9]{8,})/[a-f0-9]{8,}/', str(file_path))
        if workspace_match:
            data['workspace_id'] = workspace_match.group(1)
        
        return data
    
    def _identify_project_type(self, content: str) -> str:
        """Identify project type from markdown content.
        
        Args:
            content: Markdown content
            
        Returns:
            Project type string
        """
        content_lower = content.lower()
        
        # Check for common project indicators
        if any(word in content_lower for word in ['react', 'vue', 'angular', 'frontend']):
            return 'frontend'
        elif any(word in content_lower for word in ['api', 'backend', 'server', 'express', 'flask', 'django']):
            return 'backend'
        elif any(word in content_lower for word in ['aws', 'cloud', 'infrastructure', 'terraform', 'cdk']):
            return 'infrastructure'
        elif any(word in content_lower for word in ['mobile', 'ios', 'android', 'react native']):
            return 'mobile'
        elif any(word in content_lower for word in ['machine learning', 'ml', 'ai', 'data science']):
            return 'ml/ai'
        elif any(word in content_lower for word in ['fullstack', 'full stack', 'full-stack']):
            return 'fullstack'
        
        return 'general'
