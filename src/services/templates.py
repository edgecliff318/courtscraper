from datetime import timedelta

from src.db import bucket, db
from src.models import templates


def get_templates(
    category=None,
):
    templates_list = db.collection("templates")
    if category is not None:
        templates_list = templates_list.where("category", "==", category)

    templates_list = templates_list.stream()

    return [templates.Template(**m.to_dict()) for m in templates_list]


def get_single_template(template_id) -> templates.Template or None:
    template = db.collection("templates").document(template_id).get()
    if not template.exists:
        return None
    return templates.Template(**template.to_dict())


def get_many_templates(template_ids: list) -> list:
    templates_list = (
        db.collection("templates")
        .where("template_id", "in", template_ids)
        .stream()
    )
    return [templates.Template(**m.to_dict()) for m in templates_list]


def insert_template(template: templates.Template, filepath: str):
    # Upload the file to the templates folder in Firebase Storage
    filename = f"{template.id}.docx"

    # Upload the file to the bucket
    filepath_firebase = f"templates/{filename}"
    blob = bucket.blob(filename)
    blob.upload_from_filename(filepath)

    # Add the file path to the template
    template.filepath = filepath_firebase

    # Add the template to the database
    db.collection("templates").document(template.id).set(template.dict())

    return template


def update_template(template: templates.Template, filepath=None) -> None:
    db.collection("templates").document(template.id).update(template.dict())


def delete_template(template_id: str) -> None:
    db.collection("templates").document(template_id).delete()


def get_template_file(template_id: str, target_filepath=None):
    template = get_single_template(template_id)

    if template.filepath is None:
        raise Exception("Template file not found")
    # Load the file from the templates folder in Firebase Storage
    blob = bucket.blob(template.filepath)

    if target_filepath is None:
        # Create a temporary link to the file from Firebase Storage
        url = blob.generate_signed_url(expiration=timedelta(seconds=3600))
        return url

    # Download the file to the local
    blob.download_to_filename(target_filepath)

    # Return the file path
    return target_filepath
