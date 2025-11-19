# Requirements Document

## Introduction

The Kiro Activity Analyzer is a developer productivity tool that enables developers to self-assess their coding activities performed with the Kiro tool. The system analyzes logs, metrics, local storage contents, and session information stored in the Kiro application folder to provide insights into development workflow patterns. The solution is packaged as a Python wheel CLI that operates entirely locally to preserve developer privacy.

## Glossary

- **CLI Tool**: The command-line interface application that developers interact with to analyze their Kiro usage
- **Kiro Application Folder**: The directory at `/Users/bsubramani/Library/Application Support/Kiro` containing logs, metrics, and session data
- **Log File**: A file containing timestamped records of Kiro activities and operations
- **Metrics Report**: A structured output (CSV or JSON) containing aggregated productivity statistics
- **Date Range**: A user-specified time period for filtering analysis (e.g., last 7 days)
- **Agentic Mode**: Kiro's autonomous operation mode where the AI agent performs tasks independently
- **Tool Invocation**: An instance where Kiro uses a specific tool or function during operation
- **Activity Period**: A time window during which the developer was actively using Kiro
- **Project**: A workspace or codebase that the developer works on using Kiro, identified by workspace path or project name
- **Project Metrics**: Productivity statistics calculated specifically for a single project or workspace

## Requirements

### Requirement 1

**User Story:** As a developer, I want to analyze my Kiro logs for a specific date range, so that I can understand my productivity patterns over time

#### Acceptance Criteria

1. WHEN the developer specifies a date range parameter, THE CLI Tool SHALL parse all log files within that time period
2. WHERE the developer omits a date range, THE CLI Tool SHALL default to analyzing the last 7 days of activity
3. THE CLI Tool SHALL discover all log files in the Kiro Application Folder automatically
4. WHEN log files contain timestamps, THE CLI Tool SHALL filter entries based on the specified date range
5. IF a specified date range contains no log data, THEN THE CLI Tool SHALL display a message indicating no data was found for that period

### Requirement 2

**User Story:** As a developer, I want to see comprehensive metrics about my Kiro usage, so that I can quantify my development activity

#### Acceptance Criteria

1. THE CLI Tool SHALL calculate the total number of requests made to Kiro
2. THE CLI Tool SHALL count the number of conversations initiated during the analyzed period
3. WHEN agentic mode operations are detected, THE CLI Tool SHALL calculate the average response time in seconds
4. THE CLI Tool SHALL identify and report the fastest response time for code generation operations
5. THE CLI Tool SHALL identify and report the slowest response time for code generation operations
6. THE CLI Tool SHALL calculate the total number of characters processed across all requests
7. THE CLI Tool SHALL track which tools were invoked and the frequency of each tool usage

### Requirement 3

**User Story:** As a developer, I want insights into code generation activities, so that I can measure my coding output and success patterns

#### Acceptance Criteria

1. THE CLI Tool SHALL calculate the total lines of code generated across all activities
2. THE CLI Tool SHALL categorize lines of code by programming language
3. THE CLI Tool SHALL calculate the success rate of requests as a percentage
4. THE CLI Tool SHALL identify peak activity periods by analyzing timestamp distributions
5. THE CLI Tool SHALL generate a daily activity breakdown showing usage per day

### Requirement 4

**User Story:** As a developer, I want to export my productivity metrics in different formats, so that I can perform further analysis or share insights

#### Acceptance Criteria

1. WHEN the developer requests CSV output, THE CLI Tool SHALL generate a structured CSV file with all metrics
2. WHEN the developer requests JSON output, THE CLI Tool SHALL generate a structured JSON file with all metrics
3. THE CLI Tool SHALL store generated reports in the local file system
4. THE CLI Tool SHALL include timestamps in report filenames to prevent overwriting previous reports
5. WHERE the developer specifies an output path, THE CLI Tool SHALL save reports to that location

### Requirement 5

**User Story:** As a developer, I want a comprehensive set of CLI commands, so that I can easily access different analysis features

#### Acceptance Criteria

1. THE CLI Tool SHALL provide a command to display log file patterns and structure
2. THE CLI Tool SHALL provide a command to analyze logs for a user-specified time period
3. THE CLI Tool SHALL provide a command to discover and list all available log files in a directory
4. THE CLI Tool SHALL provide a command to generate a full metrics report
5. THE CLI Tool SHALL display help documentation when invoked with a help flag
6. WHEN the developer provides invalid command syntax, THE CLI Tool SHALL display usage instructions

### Requirement 6

**User Story:** As a developer, I want all analysis to happen locally on my machine, so that my development activity data remains private

#### Acceptance Criteria

1. THE CLI Tool SHALL perform all log parsing and analysis operations locally
2. THE CLI Tool SHALL NOT transmit any data to external servers or services
3. THE CLI Tool SHALL store all metrics reports as local files on the developer's machine
4. THE CLI Tool SHALL read data exclusively from the Kiro Application Folder
5. WHEN generating reports, THE CLI Tool SHALL write output files to local storage only

### Requirement 7

**User Story:** As a developer, I want to install the tool easily via pip, so that I can quickly set up the productivity analyzer

#### Acceptance Criteria

1. THE CLI Tool SHALL be packaged as a Python wheel file with .whl extension
2. WHEN the developer runs pip install with the wheel file, THE CLI Tool SHALL install successfully
3. THE CLI Tool SHALL register command-line entry points during installation
4. THE CLI Tool SHALL include all required dependencies in the wheel package
5. WHEN installed, THE CLI Tool SHALL be accessible from any terminal location via the command name

### Requirement 8

**User Story:** As a developer, I want the tool to be extensible, so that I can add custom metrics or integrate with other tools in the future

#### Acceptance Criteria

1. THE CLI Tool SHALL use a modular architecture that separates log parsing, analysis, and reporting components
2. THE CLI Tool SHALL define clear interfaces for adding new metric calculators
3. THE CLI Tool SHALL support plugin-style extensions for custom analysis modules
4. WHERE new log formats are introduced, THE CLI Tool SHALL allow registration of custom parsers
5. THE CLI Tool SHALL provide configuration options for enabling or disabling specific metrics

### Requirement 9

**User Story:** As a developer, I want to see metrics broken down by project, so that I can understand my productivity patterns across different codebases

#### Acceptance Criteria

1. THE CLI Tool SHALL extract project or workspace information from log entries
2. THE CLI Tool SHALL provide a command to list all projects that have been worked on during the analyzed period
3. WHEN analyzing logs, THE CLI Tool SHALL group metrics by project identifier
4. THE CLI Tool SHALL calculate all standard metrics on a per-project basis
5. THE CLI Tool SHALL generate daily breakdowns for each project showing activity per day
6. WHERE a developer specifies a project filter, THE CLI Tool SHALL display metrics only for that project
7. WHEN displaying project metrics, THE CLI Tool SHALL show project name, total activity, and key productivity indicators

### Requirement 10

**User Story:** As a developer, I want to track which LLM models I'm using with Kiro, so that I can understand my AI assistant configuration and usage patterns

#### Acceptance Criteria

1. THE CLI Tool SHALL extract the configured LLM model from Kiro settings.json
2. THE CLI Tool SHALL extract the agent-specific model selection from Kiro settings
3. THE CLI Tool SHALL track which models were actually used in log entries
4. THE CLI Tool SHALL count the frequency of each model usage from logs
5. WHEN displaying metrics, THE CLI Tool SHALL show both configured and actual model usage
6. THE CLI Tool SHALL display the agent autonomy mode (Supervised, Autopilot) from settings
