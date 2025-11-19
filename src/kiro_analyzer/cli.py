"""Main CLI entry point for Kiro Activity Analyzer."""

import click
from kiro_analyzer import __version__


@click.group()
@click.version_option(version=__version__, prog_name="kiro-analyzer")
@click.option("--verbose", is_flag=True, help="Enable verbose output")
@click.pass_context
def main(ctx: click.Context, verbose: bool) -> None:
    """Kiro Activity Analyzer - Analyze your Kiro development productivity."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


if __name__ == "__main__":
    main()
