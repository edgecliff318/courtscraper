import os

import requests
from docxtpl import DocxTemplate

from src.core.config import get_settings

settings = get_settings()


def convert_doc_to_pdf(docx_filepath):
    url = os.path.join(settings.GOTENBERG_URL, "forms/libreoffice/convert")

    payload = {}
    files = [
        ("files", open(docx_filepath, "rb")),
    ]

    response = requests.request("POST", url, data=payload, files=files)

    if response.status_code != 200:
        raise Exception(
            f"Gotenberg returned status code {response.status_code}"
        )

    pdf_file = os.path.join(
        settings.DATA_PATH, f"{os.path.basename(docx_filepath)}.pdf"
    )

    with open(pdf_file, "wb") as f:
        f.write(response.content)

    return pdf_file


class DocumentGenerator:
    def __init__(self, input_file, output_file) -> None:
        self.input_file = input_file
        self.template_file_path = input_file
        self.output_file = output_file

    def generate(self, data):
        doc = DocxTemplate(self.input_file)

        # Render the document
        doc.render(data)

        # Save the file
        doc.save(self.output_file)

    def get_context(self):
        doc = DocxTemplate(self.input_file)
        variables = doc.get_undeclared_template_variables()
        return variables
