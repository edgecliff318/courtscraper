import logging

import typer
from rich.console import Console
from rich.logging import RichHandler

from src.commands.cases import retrieve_cases as retrieve_cases_fct
from src.commands.leads import analyze_leads as analyze_leads_fct
from src.commands.leads import retrieve_leads as retrieve_leads_fct
from src.commands.leads import sync_twilio as sync_twilio_fct
from src.commands.templates import upload_templates as upload_templates_fct
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

retrieve_cases = app.command(help="Scrap the casenet website")(
    retrieve_cases_fct
)
retrieve_leads = app.command(help="Retrieve leads information")(
    retrieve_leads_fct
)
sync_twilio = app.command(help="Sync twilio interactions")(sync_twilio_fct)

analyze_leads = app.command(help="Analyze leads")(analyze_leads_fct)

upload_templates = app.command(help="Upload templates")(upload_templates_fct)

if __name__ == "__main__":
    app()
