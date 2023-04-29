import logging

import typer
from rich.console import Console
from rich.logging import RichHandler

from src.commands.cases import retrieve_cases
from src.commands.leads import retrieve_leads
from src.core.config import get_settings

settings = get_settings()

# Logging configuration
logger = logging.getLogger()
rich_handler = RichHandler()
file_handler = logging.FileHandler(filename="core.log")
rich_handler.setFormatter(
    logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")
)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")
)
rich_handler.setLevel(logging.INFO)
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(rich_handler)


app = typer.Typer()

console = Console()
console.print(
    ":rocket: [bold]Welcome to the BeenVerified Scraper[/bold] :rocket:"
)

retrieve_cases = app.command(
    help="Scrap the casenet website", no_args_is_help=True
)(retrieve_cases)
retrieve_leads = app.command(
    help="Retrieve leads information", no_args_is_help=True
)(retrieve_leads)


if __name__ == "__main__":
    app()
