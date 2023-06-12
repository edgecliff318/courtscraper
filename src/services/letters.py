import logging
import os
from datetime import timedelta

from pypdf import PdfReader, PdfWriter

from src.core.config import get_settings
from src.db import bucket
from src.services import cases

logger = logging.Logger(__name__)

settings = get_settings()


def generate_letter(case_id):
    case = cases.get_single_case(case_id)

    envelope_file = os.path.join(
        settings.ROOT_PATH, "src", "assets", "envelope_fillable.pdf"
    )
    letter_file = os.path.join(
        settings.ROOT_PATH, "src", "assets", "content_fillable.pdf"
    )

    writer_envelope = PdfWriter()
    writer_letter = PdfWriter()

    reader_envelope = PdfReader(envelope_file)
    reader_letter = PdfReader(letter_file)

    writer_envelope.append(reader_envelope)
    writer_letter.append(reader_letter)

    writer_envelope.update_page_form_field_values(
        writer_envelope.pages[0],
        {
            "address": f"{case.formatted_party_name}\n{case.formatted_party_address}"
        },
    )

    if case.first_name is None:
        case.first_name = ""

    writer_letter.update_page_form_field_values(
        writer_letter.pages[0], {"text_1bbvr": case.first_name.capitalize()}
    )

    filename_envelope = f"{case_id}_envelope.pdf"
    filename_letter = f"{case_id}_letter.pdf"

    filepath_envelope = settings.DATA_PATH.joinpath(filename_envelope)
    # Ensure the directory exists
    filepath_envelope.parent.mkdir(parents=True, exist_ok=True)

    filepath_letter = settings.DATA_PATH.joinpath(filename_letter)
    # Ensure the directory exists
    filepath_letter.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath_envelope, "wb") as output_stream:
        writer_envelope.write(output_stream)

    with open(filepath_letter, "wb") as output_stream:
        writer_letter.write(output_stream)

    # Upload the file to the bucket
    blob_envelope = bucket.blob(filename_envelope)
    blob_envelope.upload_from_filename(filepath_envelope)

    blob_letter = bucket.blob(filename_letter)
    blob_letter.upload_from_filename(filepath_letter)

    # Delete the file from local
    filepath_envelope.unlink()
    filepath_letter.unlink()

    # Get the signed url
    media_url_envelope = blob_envelope.generate_signed_url(
        expiration=timedelta(seconds=3600)
    )
    media_url_letter = blob_letter.generate_signed_url(
        expiration=timedelta(seconds=3600)
    )

    return media_url_envelope, media_url_letter
