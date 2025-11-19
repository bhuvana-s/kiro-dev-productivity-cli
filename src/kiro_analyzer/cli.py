"""Main CLI entry point for Kiro Activity Analyzer."""

import click
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from kiro_analyzer import __version__
from kiro_analyzer.services.config_manager import ConfigManager
from kiro_analyzer.services.log_discovery import LogDiscoveryService
from kiro_analyzer.parsers.parser_service import ParserService
from kiro_analyzer.services.analyzer_service import AnalyzerService
from kiro_analyzer.reporters.reporter_service import ReporterService, ReportFormat
from kiro_analyzer.analyzers import (
    ActivityPatternCalculator,
    CharacterCountCalculator,
    CodeGenerationCalculator,
    RequestCountCalculator,
    ResponseTimeCalculator,
    ToolUsageCalculator,
)


@click.group()
@click.version_option(version=__version__, prog_name="kiro-analyzer")
@click.option("--verbose", is_flag=True, help="Enable verbose output")
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to custom configuration file"
)
@click.pass_context
def main(ctx: click.Context, verbose: bool, config: Path) -> None:
    """Kiro Activity Analyzer - Analyze your Kiro development productivity.
    
    This tool analyzes logs from your Kiro application folder to provide
    insights into your development workflow patterns and productivity metrics.
    
    Examples:
    
        # Analyze last 7 days (default)
        kiro-analyzer analyze
        
        # Analyze specific date range
        kiro-analyzer analyze --start-date 2025-11-01 --end-date 2025-11-15
        
        # Generate JSON report
        kiro-analyzer analyze --output-format json --output-path report.json
        
        # Discover available log files
        kiro-analyzer discover
        
        # Show recognized log patterns
        kiro-analyzer show-patterns
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["config"] = config


@click.command()
def version() -> None:
    """Display version information."""
    click.echo(f"kiro-analyzer version {__version__}")


@click.command()
@click.option(
    "--start-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Start date for analysis (YYYY-MM-DD format)"
)
@click.option(
    "--end-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="End date for analysis (YYYY-MM-DD format)"
)
@click.option(
    "--output-format",
    type=click.Choice(["json", "csv", "console"], case_sensitive=False),
    default="console",
    help="Output format for the report"
)
@click.option(
    "--output-path",
    type=click.Path(path_type=Path),
    help="Custom path to save the report"
)
@click.pass_context
def analyze(
    ctx: click.Context,
    start_date: Optional[datetime],
    end_date: Optional[datetime],
    output_format: str,
    output_path: Optional[Path]
) -> None:
    """Analyze Kiro logs for a specified time period.
    
    This command orchestrates the full analysis pipeline:
    discovery → parsing → analysis → reporting.
    
    Examples:
    
        # Analyze last 7 days (default)
        kiro-analyzer analyze
        
        # Analyze specific date range
        kiro-analyzer analyze --start-date 2025-11-01 --end-date 2025-11-15
        
        # Generate JSON report
        kiro-analyzer analyze --output-format json --output-path report.json
    """
    verbose = ctx.obj.get("verbose", False)
    config_path = ctx.obj.get("config")
    
    try:
        # Load configuration
        config_manager = ConfigManager(config_path)
        config = config_manager.load_config()
        
        # Set default date range if not specified
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=config.default_date_range_days)
        
        if verbose:
            click.echo(f"Analyzing logs from {start_date.date()} to {end_date.date()}")
            click.echo(f"Kiro application folder: {config.kiro_app_folder}")
        
        # Step 1: Discover log files
        discovery_service = LogDiscoveryService(config.kiro_app_folder)
        log_files = discovery_service.discover_logs(
            base_path=config.kiro_app_folder,
            start_date=start_date,
            end_date=end_date
        )
        
        if not log_files:
            click.echo(
                f"No log files found in {config.kiro_app_folder} "
                f"for the period {start_date.date()} to {end_date.date()}",
                err=True
            )
            sys.exit(1)
        
        if verbose:
            click.echo(f"Discovered {len(log_files)} log files")
        
        # Step 2: Parse log files
        parser_service = ParserService()
        log_entries = parser_service.parse_files([f.path for f in log_files])
        
        if not log_entries:
            click.echo(
                "No log entries could be parsed from the discovered files",
                err=True
            )
            sys.exit(1)
        
        if verbose:
            click.echo(f"Parsed {len(log_entries)} log entries")
        
        # Step 3: Analyze log entries
        calculators = [
            RequestCountCalculator(),
            ResponseTimeCalculator(),
            CodeGenerationCalculator(),
            CharacterCountCalculator(),
            ToolUsageCalculator(),
            ActivityPatternCalculator(),
        ]
        
        analyzer_service = AnalyzerService(calculators)
        
        # Filter entries by date range
        filtered_entries = analyzer_service.filter_by_date_range(
            log_entries,
            start_date,
            end_date
        )
        
        if verbose:
            click.echo(f"Analyzing {len(filtered_entries)} entries within date range")
        
        metrics = analyzer_service.analyze(
            filtered_entries,
            analysis_period=(start_date, end_date)
        )
        
        # Step 4: Generate report
        reporter_service = ReporterService()
        format_enum = ReportFormat(output_format.lower())
        
        # Determine output path
        if output_path is None and output_format != "console":
            output_path = reporter_service.generate_timestamped_filename(
                "kiro_analysis",
                format_enum,
                config.output_directory
            )
        
        report_content = reporter_service.generate_report(
            metrics,
            format_enum,
            output_path
        )
        
        # Display or save results
        if output_format == "console":
            click.echo(report_content)
        else:
            click.echo(f"Report saved to: {output_path}")
            if verbose:
                click.echo(f"Report format: {output_format}")
        
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo(
            "\nSuggestions:\n"
            "  1. Verify Kiro is installed and has been run at least once\n"
            "  2. Check the path using: kiro-analyzer discover --directory <custom-path>\n"
            "  3. Use --help for more information",
            err=True
        )
        sys.exit(1)
    except PermissionError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo("Check that you have read permissions for the Kiro application folder", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@click.command()
@click.option(
    "--directory",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Custom directory to search for log files"
)
@click.pass_context
def discover(ctx: click.Context, directory: Optional[Path]) -> None:
    """Discover and list all available log files.
    
    This command scans the Kiro application folder (or a custom directory)
    and displays metadata about all discovered log files.
    
    Examples:
    
        # Discover logs in default Kiro folder
        kiro-analyzer discover
        
        # Discover logs in custom directory
        kiro-analyzer discover --directory /path/to/logs
    """
    verbose = ctx.obj.get("verbose", False)
    config_path = ctx.obj.get("config")
    
    try:
        # Load configuration
        config_manager = ConfigManager(config_path)
        config = config_manager.load_config()
        
        # Use custom directory if provided, otherwise use config
        search_path = directory or config.kiro_app_folder
        
        if verbose:
            click.echo(f"Searching for log files in: {search_path}")
        
        # Discover log files
        discovery_service = LogDiscoveryService(search_path)
        log_files = discovery_service.discover_logs(base_path=search_path)
        
        if not log_files:
            click.echo(f"No log files found in {search_path}")
            return
        
        # Display results
        click.echo(f"\nDiscovered {len(log_files)} log files:\n")
        
        # Group by file type
        by_type = {}
        for log_file in log_files:
            if log_file.file_type not in by_type:
                by_type[log_file.file_type] = []
            by_type[log_file.file_type].append(log_file)
        
        # Display grouped results
        for file_type, files in sorted(by_type.items()):
            click.echo(f"[{file_type.upper()}] ({len(files)} files)")
            for log_file in sorted(files, key=lambda f: f.modified_at, reverse=True):
                size_kb = log_file.size_bytes / 1024
                modified = log_file.modified_at.strftime("%Y-%m-%d %H:%M:%S")
                click.echo(f"  • {log_file.path.name}")
                click.echo(f"    Size: {size_kb:.1f} KB | Modified: {modified}")
                if verbose:
                    click.echo(f"    Path: {log_file.path}")
            click.echo()
        
        # Summary
        total_size = sum(f.size_bytes for f in log_files) / (1024 * 1024)
        click.echo(f"Total size: {total_size:.2f} MB")
        
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except PermissionError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@click.command()
@click.option(
    "--period",
    type=str,
    default="7d",
    help="Time period for analysis (e.g., 7d, 30d, 90d)"
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    help="Path to save the report"
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "csv", "console"], case_sensitive=False),
    default="console",
    help="Output format for the report"
)
@click.pass_context
def report(
    ctx: click.Context,
    period: str,
    output: Optional[Path],
    output_format: str
) -> None:
    """Generate a full metrics report for a specified period.
    
    This command converts a period specification (like '7d', '30d', '90d')
    into a date range and generates a comprehensive metrics report.
    
    Examples:
    
        # Generate report for last 7 days
        kiro-analyzer report --period 7d
        
        # Generate 30-day report as JSON
        kiro-analyzer report --period 30d --format json --output report.json
        
        # Generate 90-day report
        kiro-analyzer report --period 90d
    """
    verbose = ctx.obj.get("verbose", False)
    
    try:
        # Parse period string (e.g., "7d", "30d", "90d")
        if not period.endswith('d'):
            click.echo(
                f"Error: Invalid period format '{period}'. "
                "Expected format: <number>d (e.g., 7d, 30d, 90d)",
                err=True
            )
            sys.exit(1)
        
        try:
            days = int(period[:-1])
        except ValueError:
            click.echo(
                f"Error: Invalid period format '{period}'. "
                "Expected format: <number>d (e.g., 7d, 30d, 90d)",
                err=True
            )
            sys.exit(1)
        
        # Convert period to date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        if verbose:
            click.echo(f"Generating report for period: {period} ({start_date.date()} to {end_date.date()})")
        
        # Use the analyze command logic
        config_path = ctx.obj.get("config")
        config_manager = ConfigManager(config_path)
        config = config_manager.load_config()
        
        # Step 1: Discover log files
        discovery_service = LogDiscoveryService(config.kiro_app_folder)
        log_files = discovery_service.discover_logs(
            base_path=config.kiro_app_folder,
            start_date=start_date,
            end_date=end_date
        )
        
        if not log_files:
            click.echo(
                f"No log files found for the period {start_date.date()} to {end_date.date()}",
                err=True
            )
            sys.exit(1)
        
        if verbose:
            click.echo(f"Discovered {len(log_files)} log files")
        
        # Step 2: Parse log files
        parser_service = ParserService()
        log_entries = parser_service.parse_files([f.path for f in log_files])
        
        if not log_entries:
            click.echo("No log entries could be parsed", err=True)
            sys.exit(1)
        
        if verbose:
            click.echo(f"Parsed {len(log_entries)} log entries")
        
        # Step 3: Analyze log entries
        calculators = [
            RequestCountCalculator(),
            ResponseTimeCalculator(),
            CodeGenerationCalculator(),
            CharacterCountCalculator(),
            ToolUsageCalculator(),
            ActivityPatternCalculator(),
        ]
        
        analyzer_service = AnalyzerService(calculators)
        filtered_entries = analyzer_service.filter_by_date_range(
            log_entries,
            start_date,
            end_date
        )
        
        metrics = analyzer_service.analyze(
            filtered_entries,
            analysis_period=(start_date, end_date)
        )
        
        # Step 4: Generate report
        reporter_service = ReporterService()
        format_enum = ReportFormat(output_format.lower())
        
        # Determine output path
        if output is None and output_format != "console":
            output = reporter_service.generate_timestamped_filename(
                f"kiro_report_{period}",
                format_enum,
                config.output_directory
            )
        
        report_content = reporter_service.generate_report(
            metrics,
            format_enum,
            output
        )
        
        # Display or save results
        if output_format == "console":
            click.echo(report_content)
        else:
            click.echo(f"Report saved to: {output}")
        
    except Exception as e:
        click.echo(f"Error generating report: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@click.command(name="show-patterns")
@click.pass_context
def show_patterns(ctx: click.Context) -> None:
    """Display recognized log file patterns.
    
    This command shows all the log file patterns that the analyzer
    recognizes, along with their descriptions.
    
    Example:
    
        kiro-analyzer show-patterns
    """
    verbose = ctx.obj.get("verbose", False)
    
    try:
        # Get log patterns from discovery service
        discovery_service = LogDiscoveryService()
        patterns = discovery_service.get_log_patterns()
        
        click.echo("\nRecognized Log File Patterns:\n")
        click.echo("=" * 70)
        
        # Display patterns in a formatted table
        for pattern, description in sorted(patterns.items()):
            click.echo(f"{pattern:30} {description}")
        
        click.echo("=" * 70)
        click.echo(f"\nTotal patterns: {len(patterns)}")
        
        if verbose:
            click.echo("\nThese patterns are used to identify and categorize log files")
            click.echo("during the discovery phase of analysis.")
        
    except Exception as e:
        click.echo(f"Error displaying patterns: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


# Register commands
main.add_command(version)
main.add_command(analyze)
main.add_command(discover)
main.add_command(report)
main.add_command(show_patterns)


if __name__ == "__main__":
    main()
