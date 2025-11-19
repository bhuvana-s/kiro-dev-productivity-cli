"""Integration tests using real Kiro log files."""

import pytest
from pathlib import Path

from kiro_analyzer.parsers import KiroLogParser, MarkdownParser, ParserService
from kiro_analyzer.services import LogDiscoveryService


# Path to real Kiro application folder
KIRO_APP_FOLDER = Path("/Users/bsubramani/Library/Application Support/Kiro")


@pytest.mark.skipif(not KIRO_APP_FOLDER.exists(), reason="Kiro application folder not found")
class TestRealKiroLogs:
    """Tests using actual Kiro log files."""
    
    def test_discover_real_kiro_logs(self):
        """Test discovering actual Kiro log files."""
        discovery = LogDiscoveryService(KIRO_APP_FOLDER)
        
        # Discover logs from the last 30 days
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        logs = discovery.discover_logs(
            base_path=KIRO_APP_FOLDER,
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"\n✓ Discovered {len(logs)} log files")
        
        # Group by file type
        by_type = {}
        for log in logs:
            by_type.setdefault(log.file_type, []).append(log)
        
        for file_type, files in by_type.items():
            print(f"  - {file_type}: {len(files)} files")
        
        assert len(logs) > 0, "Should find at least some log files"
    
    def test_parse_real_kiro_agent_log(self):
        """Test parsing actual Kiro agent log file."""
        # Find the most recent Kiro Logs.log file
        log_dirs = list(KIRO_APP_FOLDER.glob("logs/*/window*/exthost/kiro.kiroAgent"))
        
        if not log_dirs:
            pytest.skip("No Kiro agent log directories found")
        
        # Get the most recent directory
        log_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        recent_dir = log_dirs[0]
        
        kiro_log = recent_dir / "Kiro Logs.log"
        if not kiro_log.exists():
            pytest.skip("Kiro Logs.log not found")
        
        print(f"\n✓ Parsing: {kiro_log}")
        
        parser = KiroLogParser()
        assert parser.can_parse(kiro_log), "Parser should recognize Kiro log file"
        
        entries = list(parser.parse(kiro_log))
        print(f"✓ Parsed {len(entries)} log entries")
        
        # Analyze event types
        event_types = {}
        for entry in entries:
            event_types[entry.event_type] = event_types.get(entry.event_type, 0) + 1
        
        print("\nEvent types found:")
        for event_type, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {event_type}: {count}")
        
        # Check for specific data extraction
        conversation_starts = [e for e in entries if e.event_type == 'conversation_start']
        tool_invocations = [e for e in entries if e.event_type == 'tool_invocation']
        
        print(f"\n✓ Found {len(conversation_starts)} conversation starts")
        print(f"✓ Found {len(tool_invocations)} tool invocations")
        
        assert len(entries) > 0, "Should parse at least some entries"
    
    def test_parse_real_q_client_log(self):
        """Test parsing actual q-client.log file."""
        log_dirs = list(KIRO_APP_FOLDER.glob("logs/*/window*/exthost/kiro.kiroAgent"))
        
        if not log_dirs:
            pytest.skip("No Kiro agent log directories found")
        
        log_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        recent_dir = log_dirs[0]
        
        q_client_log = recent_dir / "q-client.log"
        if not q_client_log.exists():
            pytest.skip("q-client.log not found")
        
        print(f"\n✓ Parsing: {q_client_log}")
        
        parser = KiroLogParser()
        entries = list(parser.parse(q_client_log))
        
        print(f"✓ Parsed {len(entries)} log entries from q-client.log")
        
        # Look for conversation data
        with_conversation_id = [e for e in entries if 'conversation_id' in e.data]
        with_tools = [e for e in entries if 'tools_used' in e.data]
        
        print(f"✓ Found {len(with_conversation_id)} entries with conversation IDs")
        print(f"✓ Found {len(with_tools)} entries with tool usage")
        
        if with_tools:
            # Show some tool names
            all_tools = set()
            for entry in with_tools[:10]:  # First 10
                tools = entry.data.get('tools_used', [])
                all_tools.update(tools)
            
            if all_tools:
                print(f"\nSample tools used: {', '.join(list(all_tools)[:5])}")
    
    def test_parse_real_markdown_files(self):
        """Test parsing actual markdown files from Kiro workspace."""
        md_files = list(KIRO_APP_FOLDER.glob("User/globalStorage/kiro.kiroagent/**/README.md"))
        
        if not md_files:
            pytest.skip("No README.md files found in Kiro workspace")
        
        print(f"\n✓ Found {len(md_files)} README.md files")
        
        parser = MarkdownParser()
        
        # Parse first few files
        parsed_count = 0
        for md_file in md_files[:5]:  # Parse first 5
            if parser.can_parse(md_file):
                entries = list(parser.parse(md_file))
                if entries:
                    entry = entries[0]
                    print(f"\n✓ Parsed: {md_file.name}")
                    if 'project_title' in entry.data:
                        print(f"  Title: {entry.data['project_title']}")
                    if 'project_type' in entry.data:
                        print(f"  Type: {entry.data['project_type']}")
                    if 'languages' in entry.data:
                        print(f"  Languages: {', '.join(entry.data['languages'])}")
                    parsed_count += 1
        
        print(f"\n✓ Successfully parsed {parsed_count} markdown files")
        assert parsed_count > 0, "Should parse at least one markdown file"
    
    def test_parser_service_with_real_files(self):
        """Test ParserService with real Kiro files."""
        service = ParserService()
        
        # Find a recent Kiro log
        log_dirs = list(KIRO_APP_FOLDER.glob("logs/*/window*/exthost/kiro.kiroAgent"))
        if not log_dirs:
            pytest.skip("No Kiro agent log directories found")
        
        log_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        recent_dir = log_dirs[0]
        
        kiro_log = recent_dir / "Kiro Logs.log"
        if not kiro_log.exists():
            pytest.skip("Kiro Logs.log not found")
        
        print(f"\n✓ Testing ParserService with: {kiro_log}")
        
        # Parse using the service
        entries = service.parse_file(kiro_log)
        
        print(f"✓ ParserService parsed {len(entries)} entries")
        assert len(entries) > 0, "Should parse entries through service"
