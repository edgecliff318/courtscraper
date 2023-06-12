import logging
import os
import shutil
import zipfile
from datetime import datetime, timedelta

from pypdf import PdfReader, PdfWriter

from src.core.config import get_settings
from src.db import bucket
from src.services import cases

logger = logging.Logger(__name__)

settings = get_settings()


def generate_single_letter(case_id, full_name, first_name, address):
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
        {"address": f"{full_name}\n{address}"},
    )

    if first_name is None:
        first_name = ""

    writer_letter.update_page_form_field_values(
        writer_letter.pages[0], {"text_1bbvr": first_name.capitalize()}
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

    return filepath_envelope, filepath_letter


def generate_letter(case_id):
    case = cases.get_single_case(case_id)

    filepath_envelope, filepath_letter = generate_single_letter(
        case_id,
        case.formatted_party_name,
        case.first_name,
        case.formatted_party_address,
    )
    filename_envelope = f"{case.case_id}_envelope.pdf"
    filename_letter = f"{case_id}_letter.pdf"

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


def generate_many_letters(case_ids):
    cases_list = cases.get_many_cases(case_ids)
    # Folder name from timestamp
    folder_name_envelope = (
        f"envelopes_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    )
    folder_path_envelope = settings.DATA_PATH.joinpath(folder_name_envelope)
    folder_path_envelope.mkdir(parents=True, exist_ok=True)

    folder_name_letter = f"letters_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    folder_path_letter = settings.DATA_PATH.joinpath(folder_name_letter)
    folder_path_letter.mkdir(parents=True, exist_ok=True)

    for case in cases_list:
        filepath_envelope, filepath_letter = generate_single_letter(
            case.case_id,
            case.formatted_party_name,
            case.first_name,
            case.formatted_party_address,
        )

        # Move the files to the folder
        filepath_envelope.rename(
            folder_path_envelope.joinpath(filepath_envelope.name)
        )

        filepath_letter.rename(
            folder_path_letter.joinpath(filepath_letter.name)
        )

    # Zip the folder
    filepath_zip_envelope = settings.DATA_PATH.joinpath(
        f"{folder_name_envelope}.zip"
    )
    filepath_zip_letter = settings.DATA_PATH.joinpath(
        f"{folder_name_letter}.zip"
    )

    with zipfile.ZipFile(filepath_zip_envelope, "w") as zip_file:
        for file in folder_path_envelope.iterdir():
            zip_file.write(file, file.name)

    with zipfile.ZipFile(filepath_zip_letter, "w") as zip_file:
        for file in folder_path_letter.iterdir():
            zip_file.write(file, file.name)

    # Upload the zip file to the bucket
    blob_zip_envelope = bucket.blob(filepath_zip_envelope.name)
    blob_zip_envelope.upload_from_filename(filepath_zip_envelope)

    blob_zip_letter = bucket.blob(filepath_zip_letter.name)
    blob_zip_letter.upload_from_filename(filepath_zip_letter)

    # Delete the folder
    shutil.rmtree(folder_path_envelope)
    shutil.rmtree(folder_path_letter)

    # Delete the zip file
    filepath_zip_envelope.unlink()
    filepath_zip_letter.unlink()

    # Get the signed url
    media_url_envelope = blob_zip_envelope.generate_signed_url(
        expiration=timedelta(seconds=3600)
    )

    media_url_letter = blob_zip_letter.generate_signed_url(
        expiration=timedelta(seconds=3600)
    )

    return media_url_envelope, media_url_letter
