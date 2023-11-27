import asyncio
import json
import logging

import typer
from rich.console import Console
from rich.progress import track

from src.core.config import get_settings
from src.scrapers import offtherecord as offtherecord_scraper

console = Console()

logger = logging.getLogger()
settings = get_settings()


def retrieve_quotes(
    headers_file: str = typer.Option(None, "--headers-file", "-f"),
    citation_code: str = typer.Option(None, "--citation-code", "-c"),
    states: str = typer.Option(None, "--states", "-s"),
    cdl: str = typer.Option("NO_CDL", "--cdl", "-d"),
    accident: bool = typer.Option(False, "--accident", "-a"),
    output_file: str = typer.Option(None, "--output-file", "-o"),
):
    console.print(
        ":rocket: [bold]Welcome to the OfftheRecord Scraper [/bold] :rocket:"
    )

    if states is not None:
        states_list = states.split(",")
    else:
        states_list = None

    if output_file is None:
        # Output file is states + citation code + cdl + accident
        output_file = f"{states}_{cdl}_{accident}.json"

    with open(headers_file) as f:
        headers = json.load(f)

    scraper = offtherecord_scraper.OffTheRecord(
        headers=headers,
        states=states_list,
        cdl=cdl,
        accident=accident,
    )
    outputs = asyncio.run(scraper.run())

    with open(output_file, "w") as f:
        json.dump(outputs, f, indent=2)

    console.print(f"Saved results to {output_file}")
