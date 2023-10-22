import datetime
import logging
import textwrap
import typing as t
from datetime import timedelta

import pandas as pd
from google.cloud.storage.retry import DEFAULT_RETRY
from PIL import Image, ImageDraw, ImageFont
from twilio.rest import Client

from src.core.config import get_settings
from src.db import bucket, db
from src.models import messages
from src.services import cases
from src.services.emails import GmailConnector

logger = logging.Logger(__name__)

settings = get_settings()


def add_text_to_image(image_url, text):
    # Get the media
    media = bucket.get_blob(image_url)

    if media is None:
        raise Exception("Media not found")

    # Download the media
    filepath = settings.DATA_PATH.joinpath(media.name)
    # Ensure the directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    modified_retry = DEFAULT_RETRY.with_delay(
        initial=1.5, multiplier=1.2, maximum=45.0
    )
    media.download_to_filename(filepath, retry=modified_retry, timeout=5)

    # Add the text to the image
    image_ticket = Image.open(filepath)
    image = Image.new(
        "RGB", (image_ticket.width, image_ticket.height + 300), (255, 255, 255)
    )
    image.paste(image_ticket, (0, 100))

    # Add disclaimer text

    draw = ImageDraw.Draw(image)

    # Font Size should depend on the image size
    font_size = min(int(image.width / 30), 40)

    # Deal with cannot open resource error
    font_file_path = settings.ROOT_PATH.joinpath(
        "src/core/fonts/outfit.ttf"
    ).as_posix()

    font = ImageFont.truetype(font_file_path, font_size)

    # Draw on top of the image center aligned
    text_width, text_height = draw.textsize(text, font=font)
    position = (
        (image.width - text_width) / 2,
        10,
    )

    draw.text(position, text, (0, 0, 255), font=font)

    # Add disclaimer text
    font = ImageFont.truetype(font_file_path, 18)
    position = (
        5,
        image.height - 200,
    )
    # Draw text in BLACK on multiple lines
    width = image.width - 2
    # Disclaimer text width for wrapping
    max_text_width = width - 2 * position[0]

    # Text width for wrapping
    disclaimer_text_width = draw.textsize(
        settings.TICKET_DISCLAIMER_TEXT, font=font
    )[0]

    line_width = len(settings.TICKET_DISCLAIMER_TEXT) / (
        round(disclaimer_text_width / max_text_width)
    )
    line_width = int(line_width)

    lines = textwrap.wrap(settings.TICKET_DISCLAIMER_TEXT, width=line_width)

    draw.multiline_text(
        position,
        "\n".join(lines),
        (0, 0, 0),
        font=font,
        align="left",
    )

    # Upload the file to the bucket
    filename = f"ads_{media.name}"

    # Delete the old file from local
    filepath.unlink()

    # Save the image to a file
    filepath = settings.DATA_PATH.joinpath(filename)
    image.save(filepath)

    # Upload the file to the bucket
    blob = bucket.blob(filename)
    blob.upload_from_filename(filepath)

    # Delete the file from local
    # filepath.unlink()

    # Get the signed url
    media_url = blob.generate_signed_url(expiration=timedelta(seconds=3600))
    return media_url, filepath


def insert_interaction(interaction):
    if interaction.id is not None:
        db.collection("interactions").document(interaction.id).set(
            interaction.model_dump()
        )
    else:
        db.collection("interactions").add(interaction.model_dump())


def update_interaction(interaction):
    db.collection("interactions").document(interaction.id).update(
        interaction.model_dump()
    )


def get_interactions(case_id=None) -> t.List[messages.Interaction]:
    if case_id is None:
        interactions = db.collection("interactions").stream()
    else:
        interactions = (
            db.collection("interactions")
            .where("case_id", "==", case_id)
            .stream()
        )

    return [messages.Interaction(**i.to_dict()) for i in interactions]


def get_interactions_filtered(
    case_id=None, start_date=None, end_date=None, direction=None
) -> t.List[messages.Interaction]:
    interactions = db.collection("interactions")
    if case_id is not None:
        interactions = interactions.where("case_id", "==", case_id)
    if start_date is not None:
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        interactions = interactions.where("creation_date", ">=", start_date)

    if end_date is not None:
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date) + timedelta(
                hours=23, minutes=59, seconds=59
            )
        interactions = interactions.where("creation_date", "<=", end_date)

    if direction is not None:
        interactions = interactions.where("direction", "==", direction)

    interactions = interactions.stream()

    return [messages.Interaction(**i.to_dict()) for i in interactions]


def get_single_interaction(interaction_id) -> messages.Interaction:
    interaction = db.collection("interactions").document(interaction_id).get()
    if interaction.exists:
        return messages.Interaction(**interaction.to_dict())
    else:
        return None


def get_messages_templates() -> t.List[messages.MessageTemplate]:
    messages_list = db.collection("messages").stream()
    return [messages.MessageTemplate(**i.to_dict()) for i in messages_list]


def get_single_message_template(message_id) -> messages.MessageTemplate:
    message = db.collection("messages").document(message_id).get()
    return messages.MessageTemplate(**message.to_dict())


def get_email_from_phone(phone, carrier):
    if carrier == "att":
        return f"{phone}@txt.att.net"
    elif carrier == "tmobile":
        return f"{phone}@tmomail.net"
    elif carrier == "verizon":
        return f"{phone}@vtext.com"
    elif carrier == "sprint":
        return f"{phone}@messaging.sprintpcs.com"
    else:
        return None


def send_message(
    case_id,
    sms_message,
    phone,
    media_enabled=False,
    method="twilio",
    carrier=None,
):
    sms_message = sms_message.replace("\\n", "\n")

    if media_enabled:
        case = cases.get_single_case(case_id)
        media_url, filepath = add_text_to_image(
            case.ticket_img, "ADVERTISEMENT"
        )
    else:
        media_url = None
        filepath = None

    # Send message
    if method == "twilio":
        client = Client(
            settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN
        )

        twilio_message = client.messages.create(
            messaging_service_sid=settings.TWILIO_MESSAGE_SERVICE_SID,
            body=sms_message,
            media_url=media_url,
            to=phone,
        )
        if twilio_message is None:
            raise Exception("Message not sent")
        status = twilio_message.status
        message_id = twilio_message.sid
        creation_date = twilio_message.date_sent

    elif method == "gmail":
        user_id = settings.SMS_EMAIL_SENDER_ID
        gmail_connector = GmailConnector(user_id=user_id)
        email = get_email_from_phone(phone, carrier)
        # Subject for the SMS message
        subject = f"SMS Message for case {case_id}"

        gmail_connector.send_email(
            subject=subject,
            message=sms_message,
            to=email,
            attachments=[
                filepath,
            ]
            if filepath is not None
            else None,
        )
        status = "sent"
        message_id = "not available"
        creation_date = datetime.datetime.now()

    else:
        raise Exception("Invalid method")

    interaction = messages.Interaction(
        case_id=case_id,
        message=sms_message,
        type="sms",
        status=status,
        id=message_id,
        direction="outbound",
        creation_date=creation_date,
        phone=phone,
    )

    # Save interaction
    insert_interaction(interaction)

    return twilio_message.status
