"""Report generation service for productivity metrics."""

import csv
import json
from datetime import datetime
from enum import Enum
from io import StringIO
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from kiro_analyzer.models import ProductivityMetrics


class ReportFormat(Enum):
    """Supported report output formats."""
    JSON = "json"
    CSV = "csv"
    CONSOLE = "console"


class ReporterService:
    """Service for generating formatted productivity reports.
    
    This service handles converting ProductivityMetrics into various output
    formats including JSON, CSV, and formatted console output.
    """
    
    def __init__(self):
        """Initialize the reporter service."""
        self.console = Console()
    
    def generate_report(
        self,
        metrics: ProductivityMetrics,
        format: ReportFormat,
        output_path: Optional[Path] = None
    ) -> str:
        """Generate a formatted report from productivity metrics.
        
        Args:
            metrics: The productivity metrics to format
            format: The desired output format (JSON, CSV, or CONSOLE)
            output_path: Optional path to save the report to disk
            
        Returns:
            The formatted report as a string
            
        Raises:
            ValueError: If an unsupported format is specified
        """
        # Route to appropriate formatter based on format type
        if format == ReportFormat.JSON:
            report_content = self._format_json(metrics)
        elif format == ReportFormat.CSV:
            report_content = self._format_csv(metrics)
        elif format == ReportFormat.CONSOLE:
            report_content = self._format_console(metrics)
        else:
            raise ValueError(f"Unsupported report format: {format}")
        
        # Save to file if output path is provided
        if output_path:
            self.save_report(report_content, output_path)
        
        return report_content
    
    def _format_json(self, metrics: ProductivityMetrics) -> str:
        """Convert ProductivityMetrics to JSON structure.
        
        Args:
            metrics: The productivity metrics to format
            
        Returns:
            Formatted JSON string with metadata and metrics
        """
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "analysis_period": {
                "start": metrics.analysis_period[0].isoformat(),
                "end": metrics.analysis_period[1].isoformat()
            },
            "metrics": {
                "total_requests": metrics.total_requests,
                "total_conversations": metrics.total_conversations,
                "avg_response_time_seconds": metrics.avg_response_time_seconds,
                "fastest_response_time_seconds": metrics.fastest_response_time_seconds,
                "slowest_response_time_seconds": metrics.slowest_response_time_seconds,
                "total_characters_processed": metrics.total_characters_processed,
                "lines_of_code_generated": metrics.lines_of_code_generated,
                "lines_by_language": metrics.lines_by_language,
                "success_rate_percent": metrics.success_rate_percent,
                "tool_usage": metrics.tool_usage,
                "peak_activity_periods": [
                    [start.isoformat(), end.isoformat()]
                    for start, end in metrics.peak_activity_periods
                ],
                "daily_breakdown": metrics.daily_breakdown
            }
        }
        
        return json.dumps(report_data, indent=2)
    
    def _format_csv(self, metrics: ProductivityMetrics) -> str:
        """Convert ProductivityMetrics to CSV rows.
        
        Args:
            metrics: The productivity metrics to format
            
        Returns:
            Formatted CSV string with metric_name, value, unit columns
        """
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=["metric_name", "value", "unit"])
        writer.writeheader()
        
        # Write all rows from the metrics
        rows = metrics.to_csv_rows()
        writer.writerows(rows)
        
        return output.getvalue()
    
    def _format_console(self, metrics: ProductivityMetrics) -> str:
        """Use rich library to create formatted tables.
        
        Args:
            metrics: The productivity metrics to format
            
        Returns:
            Formatted console output string
        """
        # Capture console output to string
        console = Console(file=StringIO(), force_terminal=True, width=100)
        
        # Create header panel
        period_start = metrics.analysis_period[0].strftime("%Y-%m-%d")
        period_end = metrics.analysis_period[1].strftime("%Y-%m-%d")
        header = Panel(
            f"[bold cyan]Kiro Activity Analysis Report[/bold cyan]\n"
            f"Period: {period_start} to {period_end}",
            border_style="cyan"
        )
        console.print(header)
        console.print()
        
        # Summary statistics table
        summary_table = Table(title="Summary Statistics", show_header=True, header_style="bold magenta")
        summary_table.add_column("Metric", style="cyan", width=40)
        summary_table.add_column("Value", justify="right", style="green")
        summary_table.add_column("Unit", style="dim")
        
        summary_table.add_row("Total Requests", str(metrics.total_requests), "count")
        summary_table.add_row("Total Conversations", str(metrics.total_conversations), "count")
        summary_table.add_row("Average Response Time", f"{metrics.avg_response_time_seconds:.2f}", "seconds")
        summary_table.add_row("Fastest Response Time", f"{metrics.fastest_response_time_seconds:.2f}", "seconds")
        summary_table.add_row("Slowest Response Time", f"{metrics.slowest_response_time_seconds:.2f}", "seconds")
        summary_table.add_row("Total Characters Processed", str(metrics.total_characters_processed), "characters")
        summary_table.add_row("Lines of Code Generated", str(metrics.lines_of_code_generated), "lines")
        summary_table.add_row("Success Rate", f"{metrics.success_rate_percent:.1f}", "percent")
        
        console.print(summary_table)
        console.print()
        
        # Lines by language table
        if metrics.lines_by_language:
            lang_table = Table(title="Code Generation by Language", show_header=True, header_style="bold magenta")
            lang_table.add_column("Language", style="cyan")
            lang_table.add_column("Lines", justify="right", style="green")
            
            for language, count in sorted(metrics.lines_by_language.items(), key=lambda x: x[1], reverse=True):
                lang_table.add_row(language, str(count))
            
            console.print(lang_table)
            console.print()
        
        # Tool usage table
        if metrics.tool_usage:
            tool_table = Table(title="Tool Usage", show_header=True, header_style="bold magenta")
            tool_table.add_column("Tool", style="cyan")
            tool_table.add_column("Count", justify="right", style="green")
            
            for tool_name, count in sorted(metrics.tool_usage.items(), key=lambda x: x[1], reverse=True):
                tool_table.add_row(tool_name, str(count))
            
            console.print(tool_table)
            console.print()
        
        # Daily breakdown table
        if metrics.daily_breakdown:
            daily_table = Table(title="Daily Activity Breakdown", show_header=True, header_style="bold magenta")
            daily_table.add_column("Date", style="cyan")
            daily_table.add_column("Activity Count", justify="right", style="green")
            daily_table.add_column("Activity Bar", style="blue")
            
            max_activity = max(metrics.daily_breakdown.values()) if metrics.daily_breakdown else 1
            for date_str, count in sorted(metrics.daily_breakdown.items()):
                bar_length = int((count / max_activity) * 30)
                bar = "█" * bar_length
                daily_table.add_row(date_str, str(count), bar)
            
            console.print(daily_table)
            console.print()
        
        # Peak activity periods
        if metrics.peak_activity_periods:
            console.print("[bold magenta]Peak Activity Periods:[/bold magenta]")
            for i, (start, end) in enumerate(metrics.peak_activity_periods, 1):
                start_str = start.strftime("%Y-%m-%d %H:%M")
                end_str = end.strftime("%H:%M")
                console.print(f"  {i}. {start_str} - {end_str}")
            console.print()
        
        # Get the string output
        return console.file.getvalue()
    
    def save_report(self, content: str, output_path: Path) -> None:
        """Save report to file.
        
        Args:
            content: The report content to save
            output_path: Path where the report should be saved
            
        Raises:
            IOError: If the file cannot be written
        """
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the report to disk
        output_path.write_text(content, encoding="utf-8")
    
    def generate_timestamped_filename(
        self,
        base_name: str,
        format: ReportFormat,
        output_dir: Optional[Path] = None
    ) -> Path:
        """Generate a timestamped filename to prevent overwriting.
        
        Args:
            base_name: Base name for the report file
            format: Report format (determines file extension)
            output_dir: Directory where the file will be saved
            
        Returns:
            Path object with timestamped filename
        """
        if output_dir is None:
            output_dir = Path.home() / ".kiro-analyzer" / "reports"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = format.value
        filename = f"{base_name}_{timestamp}.{extension}"
        
        return output_dir / filename
    
    def display_summary(self, metrics: ProductivityMetrics) -> None:
        """Display summary to console.
        
        Args:
            metrics: The productivity metrics to display
        """
        console_output = self._format_console(metrics)
        print(console_output)
