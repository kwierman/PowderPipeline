import logging

from rich.logging import RichHandler
from typer import Typer

from .analyze import analysis_app
from .backfill import backfill_app
from .scrape import scraper_app
from .visualize import viz_app

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET",
    format=FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)

app = Typer(
    help="Utilities for scraping, processing and Displaying Data from the Powder Pipeline"
)
app.add_typer(scraper_app, name="scrape")
app.add_typer(analysis_app, name="analyze")
app.add_typer(viz_app, name="visualize")
app.add_typer(backfill_app, name="backfill")
