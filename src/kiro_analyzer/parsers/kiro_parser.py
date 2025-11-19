"""Kiro-specific log parser for extracting productivity metrics."""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional, Dict, Any

from ..models import LogEntry
from .base import stream_file_lines

logger = logging.getLogger(__name__)


class KiroLogParser:
    """Parser specifically designed for Kiro application logs.
    
    This parser understands Kiro's log structure and extracts productivity-relevant
    information such as tool invocations, conversations, response times, and code generation.
    """
    
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file.
        
        Args:
            file_path: Path to the log file to check
            
        Returns:
            True if file is a Kiro log file
        """
        # Check if file is in Kiro logs directory
        path_str = str(file_path)
        if 'kiro.kiroAgent' in path_str or 'Kiro Logs.log' in path_str or 'q-client.log' in path_str:
            return True
        
        # Check if file contains Kiro-specific patterns
        if file_path.suffix.lower() == '.log':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_lines = ''.join([f.readline() for _ in range(5)])
                    if 'kiro' in first_lines.lower() or 'CodeWhisperer' in first_lines:
                        return True
            except (IOError, UnicodeDecodeError):
                pass
        
        return False
    
    def parse(self, file_path: Path) -> Iterator[LogEntry]:
        """Parse a Kiro log file and yield log entries.
        
        Args:
            file_path: Path to the log file to parse
            
        Yields:
            LogEntry objects with Kiro-specific data extracted
        """
        line_number = 0
        
        for line in stream_file_lines(file_path):
            line_number += 1
            
            # Skip empty lines
            if not line.strip():
                continue
            
            try:
                # Try to parse as structured Kiro log entry
                entry = self._parse_kiro_log_line(line, file_path)
                if entry:
                    yield entry
            except Exception as e:
                logger.debug(f"Could not parse line {line_number} in {file_path}: {e}")
                continue
    
    def _parse_kiro_log_line(self, line: str, file_path: Path) -> Optional[LogEntry]:
        """Parse a single Kiro log line.
        
        Args:
            line: Log line to parse
            file_path: Source file path
            
        Returns:
            LogEntry if successfully parsed, None otherwise
        """
        # Pattern: YYYY-MM-DD HH:MM:SS.mmm [level] message
        timestamp_pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\s+\[(\w+)\]\s+(.+)$'
        match = re.match(timestamp_pattern, line)
        
        if not match:
            return None
        
        timestamp_str, level, message = match.groups()
        
        # Parse timestamp
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            return None
        
        # Extract structured data from message
        data = self._extract_kiro_data(message, level)
        
        # Determine event type
        event_type = self._determine_event_type(message, data)
        
        return LogEntry(
            timestamp=timestamp,
            event_type=event_type,
            data=data,
            raw_line=line,
            source_file=file_path
        )
    
    def _extract_kiro_data(self, message: str, level: str) -> Dict[str, Any]:
        """Extract structured data from Kiro log message.
        
        Args:
            message: Log message content
            level: Log level (info, error, warning, etc.)
            
        Returns:
            Dictionary of extracted data
        """
        data = {'level': level, 'message': message}
        
        # Try to parse JSON content in message
        json_match = re.search(r'\{.*\}', message)
        if json_match:
            try:
                json_data = json.loads(json_match.group())
                data['json_payload'] = json_data
                
                # Extract specific Kiro metrics
                self._extract_conversation_data(json_data, data)
                self._extract_tool_usage(json_data, data)
                self._extract_code_generation(json_data, data)
                
            except json.JSONDecodeError:
                pass
        
        # Extract agent controller events
        if '[agent-controller]' in message:
            data['agent_event'] = True
            if 'Triggered new agent' in message:
                data['event_subtype'] = 'agent_start'
                # Extract autonomy mode
                if 'autonomyMode=' in message:
                    mode_match = re.search(r'autonomyMode=(\w+)', message)
                    if mode_match:
                        data['autonomy_mode'] = mode_match.group(1)
        
        # Extract tool invocations
        if '[Tool agent Action]' in message or 'toolUse' in message:
            data['tool_invocation'] = True
        
        # Extract terminal commands
        if '[Terminal]' in message and 'Executing command' in message:
            data['terminal_command'] = True
        
        return data
    
    def _extract_conversation_data(self, json_data: dict, data: dict) -> None:
        """Extract conversation-related data from JSON payload.
        
        Args:
            json_data: Parsed JSON data
            data: Data dictionary to update
        """
        if 'conversationId' in json_data:
            data['conversation_id'] = json_data['conversationId']
        
        if 'conversationState' in json_data:
            conv_state = json_data['conversationState']
            if 'conversationId' in conv_state:
                data['conversation_id'] = conv_state['conversationId']
            if 'agentTaskType' in conv_state:
                data['task_type'] = conv_state['agentTaskType']
            
            # Extract message history length
            if 'history' in conv_state:
                data['message_count'] = len(conv_state['history'])
    
    def _extract_tool_usage(self, json_data: dict, data: dict) -> None:
        """Extract tool usage information from JSON payload.
        
        Args:
            json_data: Parsed JSON data
            data: Data dictionary to update
        """
        # Extract tool uses from assistant responses
        if 'toolUses' in json_data:
            tool_uses = json_data['toolUses']
            if isinstance(tool_uses, list):
                data['tools_used'] = [
                    tool.get('name', 'unknown') for tool in tool_uses if isinstance(tool, dict)
                ]
                data['tool_count'] = len(tool_uses)
        
        # Extract tool results
        if 'toolResults' in json_data:
            tool_results = json_data['toolResults']
            if isinstance(tool_results, list):
                data['tool_results_count'] = len(tool_results)
                # Count successful vs failed
                successes = sum(1 for r in tool_results if isinstance(r, dict) and r.get('status') == 'success')
                data['tool_success_count'] = successes
                data['tool_failure_count'] = len(tool_results) - successes
        
        # Extract available tools
        if 'tools' in json_data:
            tools = json_data['tools']
            if isinstance(tools, list):
                data['available_tools_count'] = len(tools)
    
    def _extract_code_generation(self, json_data: dict, data: dict) -> None:
        """Extract code generation metrics from JSON payload.
        
        Args:
            json_data: Parsed JSON data
            data: Data dictionary to update
        """
        # Look for content that might contain code
        if 'content' in json_data:
            content = json_data['content']
            if isinstance(content, str):
                # Estimate lines of code (rough heuristic)
                lines = content.count('\n')
                if lines > 5:  # Likely contains code if many lines
                    data['potential_code_lines'] = lines
                
                # Count characters
                data['content_length'] = len(content)
        
        # Extract model information
        if 'modelId' in json_data:
            data['model_id'] = json_data['modelId']
        
        # Extract response metadata
        if 'metadata' in json_data:
            metadata = json_data['metadata']
            if isinstance(metadata, dict):
                if 'httpStatusCode' in metadata:
                    data['http_status'] = metadata['httpStatusCode']
                if 'requestId' in metadata:
                    data['request_id'] = metadata['requestId']
    
    def _determine_event_type(self, message: str, data: dict) -> str:
        """Determine the event type from message and extracted data.
        
        Args:
            message: Log message
            data: Extracted data dictionary
            
        Returns:
            Event type string
        """
        # Check for specific event types
        if data.get('agent_event'):
            if data.get('event_subtype') == 'agent_start':
                return 'conversation_start'
            return 'agent_event'
        
        if data.get('tool_invocation'):
            return 'tool_invocation'
        
        if data.get('terminal_command'):
            return 'terminal_command'
        
        if 'conversation_id' in data:
            if 'toolUses' in message or data.get('tools_used'):
                return 'assistant_response'
            if 'userInputMessage' in message:
                return 'user_request'
            return 'conversation_message'
        
        if 'GenerateAssistantResponseCommand' in message:
            return 'llm_request'
        
        # Default based on level
        level = data.get('level', '').lower()
        if level == 'error':
            return 'error'
        elif level == 'warning':
            return 'warning'
        
        return 'info'
