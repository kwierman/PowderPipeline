import logging
from pathlib import Path

from rich.console import Console
from typer import Typer

from ..config import load_settings
from ..warehouse import get_session

console = Console()
logger = logging.getLogger(__name__)

backfill_app = Typer(help="Commands for backfilling ski pass data")


@backfill_app.command("ski-resorts")
def backfill_ski_resorts(config_file: Path = Path("config.yaml")):
    """
    Scrape ski resort data from OnTheSnow.
    """
    settings = load_settings(config_file)
    with get_session(settings) as session:
        console.print(
            f"[blue]Scraping ski resort data using settings from {config_file}...[/blue]"
        )
        console.print("[yellow]Note: This command is not yet implemented.[/yellow]")
