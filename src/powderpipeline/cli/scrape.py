import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from typer import Typer

from ..config import load_settings
from ..scrapers.ski_resorts import SkiResortScraper
from ..warehouse import get_session

console = Console()
logger = logging.getLogger(__name__)

scraper_app = Typer(help="Commands for scraping ski pass data")

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)],
)


@scraper_app.command("ski-resorts")
def scrape_ski_resorts(
    config_file: Path = Path("config.yaml"),
    headless: bool = False,
):
    """
    Scrape ski resort data from OnTheSnow.
    """
    settings = load_settings(config_file)
    with get_session(settings) as session:
        console.print(
            f"[blue]Scraping ski resort data using settings from {config_file}...[/blue]"
        )
        with SkiResortScraper(
            session=session,
            writer=None,
            settings=settings,
            headless=headless,
        ) as scraper:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    "[cyan]Scraping ski resorts worldwide...", total=None
                )
                scraper.scrape()
                progress.update(task, completed=True)

        console.print("[green]Scraping complete![/green]")
