# Design Document

## Overview

The Kiro Activity Analyzer is a Python-based CLI tool that analyzes developer productivity by parsing and aggregating metrics from Kiro application logs and data files. The tool follows a modular architecture with clear separation between log discovery, parsing, analysis, and reporting layers. It is distributed as a Python wheel package and operates entirely locally to ensure data privacy.

### Key Design Principles

- **Privacy First**: All operations are local; no external data transmission
- **Extensibility**: Plugin-based architecture for custom metrics and parsers
- **Usability**: Intuitive CLI with sensible defaults and clear output
- **Performance**: Efficient log parsing with streaming and caching strategies
- **Maintainability**: Clean separation of concerns with well-defined interfaces

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                            │
│  (Command parsing, argument validation, output formatting)   │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    Service Layer                             │
│  (Business logic, orchestration, date range filtering)       │
└────┬───────────────┬───────────────┬────────────────────────┘
     │               │               │
┌────▼─────┐  ┌─────▼──────┐  ┌────▼──────────┐
│ Discovery│  │   Parser   │  │   Analyzer    │
│  Service │  │  Service   │  │   Service     │
└────┬─────┘  └─────┬──────┘  └────┬──────────┘
     │               │               │
┌────▼───────────────▼───────────────▼──────────────────────┐
│                    Data Layer                              │
│  (File I/O, log reading, metrics storage)                  │
└────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
User Command → CLI Parser → Service Orchestrator → Discovery Service
                                    ↓
                            Parser Service (parse logs)
                                    ↓
                            Analyzer Service (compute metrics)
                                    ↓
                            Reporter Service (generate output)
                                    ↓
                            Output (CSV/JSON/Console)
```

## Components and Interfaces

### 1. CLI Layer

**Purpose**: Handle user interaction, command parsing, and output formatting

**Components**:

- `cli.py`: Main entry point using Click or argparse framework
- `commands/`: Directory containing command implementations
  - `analyze.py`: Log analysis command
  - `discover.py`: Log discovery command
  - `report.py`: Report generation command
  - `show_patterns.py`: Display log patterns command

**Key Interfaces**:

```python
class CLICommand(Protocol):
    """Base protocol for CLI commands"""
    def execute(self, args: Dict[str, Any]) -> int:
        """Execute command and return exit code"""
        ...

class OutputFormatter(Protocol):
    """Format output for display"""
    def format_metrics(self, metrics: MetricsData) -> str:
        ...
    def format_table(self, data: List[Dict]) -> str:
        ...
```

**Command Structure**:

```
kiro-analyzer analyze --start-date YYYY-MM-DD --end-date YYYY-MM-DD [--output-format json|csv]
kiro-analyzer discover --directory PATH
kiro-analyzer report --period 7d [--output PATH]
kiro-analyzer show-patterns
```

### 2. Discovery Service

**Purpose**: Locate and catalog log files in the Kiro Application Folder

**Responsibilities**:
- Scan directory structure for log files
- Identify log file types and formats
- Filter files by date range
- Cache file metadata for performance

**Key Interfaces**:

```python
@dataclass
class LogFileMetadata:
    path: Path
    file_type: str  # 'activity', 'metrics', 'session'
    size_bytes: int
    created_at: datetime
    modified_at: datetime
    
class LogDiscoveryService:
    def discover_logs(
        self, 
        base_path: Path, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[LogFileMetadata]:
        """Discover log files within date range"""
        ...
    
    def get_log_patterns(self) -> Dict[str, str]:
        """Return recognized log file patterns"""
        ...
```

### 3. Parser Service

**Purpose**: Parse log files and extract structured data

**Responsibilities**:
- Read log files efficiently (streaming for large files)
- Parse different log formats (JSON, plain text, structured logs)
- Extract timestamps, events, and metadata
- Handle malformed or incomplete log entries

**Key Interfaces**:

```python
@dataclass
class LogEntry:
    timestamp: datetime
    event_type: str
    data: Dict[str, Any]
    raw_line: str
    
class LogParser(Protocol):
    """Base protocol for log parsers"""
    def can_parse(self, file_path: Path) -> bool:
        """Check if parser can handle this file"""
        ...
    
    def parse(self, file_path: Path) -> Iterator[LogEntry]:
        """Parse log file and yield entries"""
        ...

class ParserRegistry:
    """Registry for pluggable parsers"""
    def register_parser(self, parser: LogParser) -> None:
        ...
    
    def get_parser(self, file_path: Path) -> Optional[LogParser]:
        ...
```

**Parser Implementations**:
- `JSONLogParser`: For JSON-formatted logs
- `PlainTextLogParser`: For plain text logs with regex patterns
- `StructuredLogParser`: For structured log formats

### 4. Analyzer Service

**Purpose**: Compute metrics and insights from parsed log data

**Responsibilities**:
- Aggregate statistics across log entries
- Calculate productivity metrics
- Identify patterns and trends
- Generate time-series data for activity periods

**Key Interfaces**:

```python
@dataclass
class ProductivityMetrics:
    total_requests: int
    total_conversations: int
    avg_response_time_seconds: float
    fastest_response_time_seconds: float
    slowest_response_time_seconds: float
    total_characters_processed: int
    lines_of_code_generated: int
    lines_by_language: Dict[str, int]
    success_rate_percent: float
    tool_usage: Dict[str, int]
    peak_activity_periods: List[Tuple[datetime, datetime]]
    daily_breakdown: Dict[str, int]  # date -> activity count

class MetricCalculator(Protocol):
    """Base protocol for metric calculators"""
    def calculate(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """Calculate specific metrics from log entries"""
        ...

class AnalyzerService:
    def __init__(self, calculators: List[MetricCalculator]):
        self.calculators = calculators
    
    def analyze(self, entries: List[LogEntry]) -> ProductivityMetrics:
        """Analyze log entries and compute all metrics"""
        ...
    
    def filter_by_date_range(
        self, 
        entries: List[LogEntry],
        start_date: datetime,
        end_date: datetime
    ) -> List[LogEntry]:
        """Filter entries within date range"""
        ...
```

**Metric Calculator Implementations**:
- `RequestCountCalculator`
- `ResponseTimeCalculator`
- `CodeGenerationCalculator`
- `ToolUsageCalculator`
- `ActivityPatternCalculator`

### 5. Reporter Service

**Purpose**: Generate formatted output reports

**Responsibilities**:
- Format metrics for different output types (CSV, JSON, console)
- Generate summary statistics
- Create visualizations (ASCII charts for console)
- Save reports to disk

**Key Interfaces**:

```python
class ReportFormat(Enum):
    JSON = "json"
    CSV = "csv"
    CONSOLE = "console"

class ReporterService:
    def generate_report(
        self,
        metrics: ProductivityMetrics,
        format: ReportFormat,
        output_path: Optional[Path] = None
    ) -> str:
        """Generate formatted report"""
        ...
    
    def save_report(self, content: str, output_path: Path) -> None:
        """Save report to file"""
        ...
    
    def display_summary(self, metrics: ProductivityMetrics) -> None:
        """Display summary to console"""
        ...
```

### 6. Configuration Manager

**Purpose**: Manage tool configuration and user preferences

**Key Interfaces**:

```python
@dataclass
class AnalyzerConfig:
    kiro_app_folder: Path
    default_date_range_days: int = 7
    output_directory: Path = Path.home() / ".kiro-analyzer" / "reports"
    enabled_metrics: List[str] = field(default_factory=list)
    custom_parsers: List[str] = field(default_factory=list)

class ConfigManager:
    def load_config(self) -> AnalyzerConfig:
        """Load configuration from file or defaults"""
        ...
    
    def save_config(self, config: AnalyzerConfig) -> None:
        """Save configuration to file"""
        ...
```

## Data Models

### Core Data Structures

```python
# Log Entry Model
@dataclass
class LogEntry:
    timestamp: datetime
    event_type: str  # 'request', 'response', 'tool_invocation', 'conversation_start'
    data: Dict[str, Any]
    raw_line: str
    source_file: Path

# Metrics Model
@dataclass
class ProductivityMetrics:
    analysis_period: Tuple[datetime, datetime]
    total_requests: int
    total_conversations: int
    avg_response_time_seconds: float
    fastest_response_time_seconds: float
    slowest_response_time_seconds: float
    total_characters_processed: int
    lines_of_code_generated: int
    lines_by_language: Dict[str, int]
    success_rate_percent: float
    tool_usage: Dict[str, int]
    peak_activity_periods: List[Tuple[datetime, datetime]]
    daily_breakdown: Dict[str, int]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        ...
    
    def to_csv_rows(self) -> List[Dict[str, Any]]:
        """Convert to rows for CSV output"""
        ...

# Report Model
@dataclass
class AnalysisReport:
    generated_at: datetime
    metrics: ProductivityMetrics
    metadata: Dict[str, Any]  # version, config, etc.
```

### File Format Specifications

**JSON Report Format**:
```json
{
  "generated_at": "2025-11-19T10:30:00Z",
  "analysis_period": {
    "start": "2025-11-12T00:00:00Z",
    "end": "2025-11-19T23:59:59Z"
  },
  "metrics": {
    "total_requests": 150,
    "total_conversations": 25,
    "avg_response_time_seconds": 2.5,
    "fastest_response_time_seconds": 0.8,
    "slowest_response_time_seconds": 8.2,
    "total_characters_processed": 45000,
    "lines_of_code_generated": 1200,
    "lines_by_language": {
      "python": 800,
      "javascript": 300,
      "typescript": 100
    },
    "success_rate_percent": 92.5,
    "tool_usage": {
      "file_read": 45,
      "file_write": 30,
      "bash_execute": 20
    },
    "peak_activity_periods": [
      ["2025-11-15T14:00:00Z", "2025-11-15T16:00:00Z"],
      ["2025-11-18T10:00:00Z", "2025-11-18T12:00:00Z"]
    ],
    "daily_breakdown": {
      "2025-11-12": 18,
      "2025-11-13": 22,
      "2025-11-14": 15
    }
  }
}
```

**CSV Report Format**:
```csv
metric_name,value,unit
total_requests,150,count
total_conversations,25,count
avg_response_time,2.5,seconds
fastest_response_time,0.8,seconds
slowest_response_time,8.2,seconds
total_characters_processed,45000,characters
lines_of_code_generated,1200,lines
success_rate,92.5,percent
```

## Error Handling

### Error Categories

1. **File System Errors**
   - Missing Kiro application folder
   - Insufficient permissions
   - Corrupted log files

2. **Parsing Errors**
   - Malformed log entries
   - Unknown log formats
   - Encoding issues

3. **Analysis Errors**
   - Insufficient data for metrics
   - Invalid date ranges
   - Missing required fields

4. **Output Errors**
   - Unable to write report files
   - Invalid output format specified

### Error Handling Strategy

```python
class AnalyzerError(Exception):
    """Base exception for analyzer errors"""
    pass

class LogDiscoveryError(AnalyzerError):
    """Errors during log discovery"""
    pass

class LogParsingError(AnalyzerError):
    """Errors during log parsing"""
    pass

class MetricsCalculationError(AnalyzerError):
    """Errors during metrics calculation"""
    pass

class ReportGenerationError(AnalyzerError):
    """Errors during report generation"""
    pass

# Error handling approach
def safe_parse_log(file_path: Path) -> List[LogEntry]:
    """Parse log with error recovery"""
    entries = []
    errors = []
    
    try:
        for line_num, line in enumerate(read_file(file_path)):
            try:
                entry = parse_line(line)
                entries.append(entry)
            except ParseError as e:
                errors.append((line_num, str(e)))
                # Continue parsing remaining lines
    except IOError as e:
        raise LogParsingError(f"Cannot read file {file_path}: {e}")
    
    if errors:
        log_warning(f"Encountered {len(errors)} parsing errors in {file_path}")
    
    return entries
```

### User-Facing Error Messages

- Clear, actionable error messages
- Suggestions for resolution
- Debug mode for detailed error information

Example:
```
Error: Cannot find Kiro application folder at /Users/bsubramani/Library/Application Support/Kiro

Suggestions:
  1. Verify Kiro is installed and has been run at least once
  2. Check the path using: kiro-analyzer discover --directory <custom-path>
  3. Use --help for more information
```

## Testing Strategy

### Unit Testing

**Scope**: Individual components and functions

**Test Coverage**:
- Log parsers with various log formats
- Metric calculators with edge cases
- Date range filtering logic
- Output formatters for each format type

**Tools**: pytest, pytest-cov for coverage

**Example Test Structure**:
```python
def test_json_log_parser_valid_entry():
    parser = JSONLogParser()
    entry = parser.parse_line('{"timestamp": "2025-11-19T10:00:00Z", "event": "request"}')
    assert entry.event_type == "request"
    assert entry.timestamp.year == 2025

def test_request_count_calculator():
    entries = [create_mock_entry("request") for _ in range(10)]
    calculator = RequestCountCalculator()
    result = calculator.calculate(entries)
    assert result["total_requests"] == 10
```

### Integration Testing

**Scope**: Component interactions and end-to-end flows

**Test Scenarios**:
- Full analysis pipeline from discovery to report generation
- Multiple log file types processed together
- Date range filtering across services
- Report generation in all formats

**Tools**: pytest with fixtures for test data

### Functional Testing

**Scope**: CLI commands and user workflows

**Test Scenarios**:
- Each CLI command with various argument combinations
- Error handling for invalid inputs
- Output verification for different formats
- Configuration loading and saving

**Tools**: pytest with subprocess or Click's testing utilities

### Test Data

- Sample log files representing different scenarios
- Edge cases: empty logs, malformed entries, large files
- Fixtures for common test data structures

## Deployment and Installation

### Package Structure

```
kiro-analyzer/
├── pyproject.toml
├── setup.py
├── README.md
├── LICENSE
├── src/
│   └── kiro_analyzer/
│       ├── __init__.py
│       ├── cli.py
│       ├── commands/
│       ├── services/
│       ├── parsers/
│       ├── analyzers/
│       ├── reporters/
│       └── utils/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
└── docs/
```

### Build Configuration (pyproject.toml)

```toml
[build-system]
requires = ["setuptools>=65.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "kiro-analyzer"
version = "0.1.0"
description = "Developer productivity analyzer for Kiro"
authors = [{name = "Developer", email = "dev@example.com"}]
requires-python = ">=3.9"
dependencies = [
    "click>=8.0",
    "python-dateutil>=2.8",
    "pandas>=1.5",
    "rich>=13.0"  # For beautiful console output
]

[project.scripts]
kiro-analyzer = "kiro_analyzer.cli:main"

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "black>=23.0",
    "mypy>=1.0",
    "ruff>=0.1"
]
```

### Installation Process

1. Build wheel: `python -m build`
2. Install: `pip install dist/kiro_analyzer-0.1.0-py3-none-any.whl`
3. Verify: `kiro-analyzer --version`

### Dependencies

**Core Dependencies**:
- `click`: CLI framework
- `python-dateutil`: Date parsing and manipulation
- `pandas`: Data manipulation for metrics (optional, for advanced features)
- `rich`: Beautiful console output with tables and progress bars

**Development Dependencies**:
- `pytest`: Testing framework
- `pytest-cov`: Code coverage
- `black`: Code formatting
- `mypy`: Type checking
- `ruff`: Fast linting

## Extensibility Design

### Plugin Architecture

**Custom Parsers**:
```python
# User creates custom parser
class CustomLogParser(LogParser):
    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix == ".custom"
    
    def parse(self, file_path: Path) -> Iterator[LogEntry]:
        # Custom parsing logic
        ...

# Register via configuration
config = AnalyzerConfig(
    custom_parsers=["mypackage.parsers.CustomLogParser"]
)
```

**Custom Metrics**:
```python
# User creates custom metric calculator
class CustomMetricCalculator(MetricCalculator):
    def calculate(self, entries: List[LogEntry]) -> Dict[str, Any]:
        # Custom metric logic
        return {"custom_metric": value}

# Register programmatically
analyzer = AnalyzerService()
analyzer.register_calculator(CustomMetricCalculator())
```

### Configuration Extension Points

- Custom log file patterns
- Additional output formats
- Metric calculation plugins
- Custom report templates

## Performance Considerations

### Optimization Strategies

1. **Streaming Parsing**: Process large log files line-by-line without loading entire file into memory
2. **Caching**: Cache parsed log metadata to avoid re-scanning unchanged files
3. **Parallel Processing**: Use multiprocessing for analyzing multiple log files concurrently
4. **Lazy Loading**: Load and parse only files within the specified date range
5. **Incremental Analysis**: Support incremental updates for continuous monitoring

### Performance Targets

- Parse 1GB of log data in under 30 seconds
- Support log files up to 10GB
- Memory usage under 500MB for typical analysis
- CLI response time under 2 seconds for cached operations

## Security and Privacy

### Privacy Guarantees

- No network communication
- All data processing happens locally
- No telemetry or usage tracking
- Reports stored only on local filesystem

### Security Considerations

- Validate all file paths to prevent directory traversal
- Sanitize user inputs in CLI commands
- Handle sensitive data in logs appropriately
- Secure file permissions for generated reports

## Future Enhancements

### Potential Extensions

1. **Real-time Monitoring**: Background daemon mode for continuous analysis
2. **Web Dashboard**: Local web interface for visualizing metrics
3. **Comparative Analysis**: Compare productivity across different time periods
4. **Team Analytics**: Aggregate anonymized metrics across team members
5. **Integration with IDEs**: Plugin for VS Code or other editors
6. **Machine Learning**: Predict productivity patterns and suggest optimizations
7. **Export to External Tools**: Integration with productivity tracking services
