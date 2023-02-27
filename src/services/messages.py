import logging
import os
from typing import List

from twilio.rest import Client

from src.core.config import get_settings
from src.db import db
from src.models import messages

logger = logging.Logger(__name__)

settings = get_settings()


def send_message(case_id, sms_message, phone, media_enabled=False):
    # Send message
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    if media_enabled:
        media_url = os.path.join(settings.SITE_URL, f"images/{case_id}.png")
        media_url = f"{media_url}?api_key={settings.API_KEY}"
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


def get_interactions(case_id) -> List[messages.Interaction]:
    interactions = (
        db.collection("interactions").where("case_id", "==", case_id).stream()
    )

    return [messages.Interaction(**i.to_dict()) for i in interactions]


def get_single_interaction(interaction_id) -> messages.Interaction:
    interaction = db.collection("interactions").document(interaction_id).get()
    return messages.Interaction(**interaction.to_dict())


def get_messages_templates() -> List[messages.MessageTemplate]:
    messages = db.collection("message_templates").stream()

    return [messages.MessageTemplate(**i.to_dict()) for i in messages]
