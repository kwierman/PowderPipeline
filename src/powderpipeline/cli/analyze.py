import logging
from pathlib import Path

from rich.console import Console
from typer import Typer

from ..analyzers.snow import SnowAnalyzer
from ..config import load_settings
from ..warehouse import get_session

console = Console()
logger = logging.getLogger(__name__)

analysis_app = Typer(help="Commands for analyzing ski pass data")
console = Console()


@analysis_app.command("snow")
def snow(
    config_file: Path = Path("config.yaml"),
):
    """
    Scrape ski resort data from OnTheSnow.
    """
    settings = load_settings(config_file)
    with get_session(settings) as session:
        console.print(
            f"[blue]Analyzing ski resort data using settings from {config_file}...[/blue]"
        )
        snow_analyzer = SnowAnalyzer(session, settings)
        snow_analyzer.run()

        console.print("[green]Analysis complete![/green]")
