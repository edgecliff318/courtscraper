import json
import logging

import pandas as pd
import typer
from docxtpl import DocxTemplate
from rich.console import Console
from rich.progress import track

from src.core.config import get_settings
from src.models import templates as templates_model
from src.services import templates as templates_service

console = Console()
console.print(
    ":rocket: [bold]Welcome to the Template Uploader[/bold] :rocket:"
)


console = Console()

logger = logging.getLogger()
settings = get_settings()


def upload_templates_csv(input_file: str):
    templates_csv = pd.read_csv(input_file)

    for template in track(templates_csv.to_dict("records")):
        console.print(f"Processing template {template['Name']}...")
        with console.status(
            f"Validating the template {template['Name']} file...",
            spinner="dots",
        ) as status:
            template_file = None
            try:
                template_file = template["Template File "]
                # urldecode the template file
                template_file = template_file.replace("%20", " ")
                doc = DocxTemplate(f"templates/{template_file}")
                doc.get_undeclared_template_variables()
                status.update(
                    f"Validating the template {template['Name']} file... [green]Done![/green]"
                )
            except Exception:
                status.update(
                    f"Validating the template {template['Name']} file... [red]Error![/red]"
                )
                console.print(f"File is invalid {template_file}")
                continue

        # Insert the template
        template_name = template.get("Name", "0.docx").split(".")[0]
        if template_name == "0":
            console.print(
                f"[red]Error![/red] Invalid template name for {template}"
            )
            continue
        template_instance = templates_model.Template(
            id=f"MO_{template_name}",
            name=f"{template_name}",
            category="court",
            filepath=f"templates/{template_name}",
            parameters={
                "attachments": template.get("Attachments", "No Attachment"),
                "naming_convention": template.get(
                    "Naming Convention", "No Naming Convention"
                ),
                "sub_category": template.get(
                    "Sub Category", "No Sub Category"
                ),
                "category": template.get("Category", "No Category"),
            },
            state="MO",
        )

        templates_service.insert_template(
            template_instance, f"templates/{template_file}"
        )
        console.print(
            f"Template {template['Name']} inserted successfully!",
        )


def upload_templates_json(input_file: str):
    templates_json = json.load(open(input_file))

    for template in track(templates_json):
        console.print(f"Processing template {template['name']}...")
        template_instance = templates_model.Template(
            id=template.get("id"),
            name=template.get("name"),
            category=template.get("category"),
            filepath=template.get("filepath"),
            type=template.get("type"),
            parameters=template.get("parameters"),
            state=template.get("state"),
            text=template.get("text"),
            subject=template.get("subject"),
        )

        templates_service.insert_template(
            template_instance, template.get("filepath")
        )
        console.print(
            f"Template {template['name']} inserted successfully!",
        )


def upload_templates(input_file: str):
    # If Json file
    if input_file.endswith(".csv"):
        upload_templates_csv(input_file)

    if input_file.endswith(".json"):
        upload_templates_json(input_file)


if __name__ == "__main__":
    typer.run(upload_templates_csv)
