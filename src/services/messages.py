import logging
import textwrap
import typing as t
from datetime import timedelta

from PIL import Image, ImageDraw, ImageFont
from twilio.rest import Client

from src.core.config import get_settings
from src.db import bucket, db
from src.models import messages
from src.services import cases

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
    media.download_to_filename(filepath)

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
    font = ImageFont.truetype("Arial.ttf", 18)
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
    filepath.unlink()

    # Get the signed url
    media_url = blob.generate_signed_url(expiration=timedelta(seconds=3600))
    return media_url


def send_message(case_id, sms_message, phone, media_enabled=False):
    # Send message
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    sms_message = sms_message.replace("\\n", "\n")

    if media_enabled:
        case = cases.get_single_case(case_id)
        media_url = add_text_to_image(case.ticket_img, "ADVERTISEMENT")
    else:
        media_url = None

    twilio_message = client.messages.create(
        messaging_service_sid=settings.TWILIO_MESSAGE_SERVICE_SID,
        body=sms_message,
        media_url=media_url,
        to=phone,
    )

    interaction = messages.Interaction(
        case_id=case_id,
        message=sms_message,
        type="sms",
        status=twilio_message.status,
    )

    # Save interaction
    db.collection("interactions").add(interaction.dict())

    return twilio_message.status


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


def get_single_interaction(interaction_id) -> messages.Interaction:
    interaction = db.collection("interactions").document(interaction_id).get()
    return messages.Interaction(**interaction.to_dict())


def get_messages_templates() -> t.List[messages.MessageTemplate]:
    messages_list = db.collection("messages").stream()
    return [messages.MessageTemplate(**i.to_dict()) for i in messages_list]


def get_single_message_template(message_id) -> messages.MessageTemplate:
    message = db.collection("messages").document(message_id).get()
    return messages.MessageTemplate(**message.to_dict())


def save_message_status(message: t.Dict):
    try:
        db.collection("messageStatus").add(message)
    except Exception as e:
        logger.error(e)
        return False
    return True


def get_message_status(message_id):
    message = db.collection("messageStatus").get()
    return message.to_dict()
