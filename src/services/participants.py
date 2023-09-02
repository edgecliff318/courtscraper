from datetime import datetime
from typing import MutableMapping, Optional

from google.cloud.firestore_v1.base_query import FieldFilter, Or
from google.cloud.firestore_v1.field_path import FieldPath
from pydantic import ValidationError

from src.db import db
from src.models import participants


def get_participants(role=None):
    if role is None:
        output = db.collection("participants").stream()

    else:
        output = (
            db.collection("participants").where("role", "==", role).stream()
        )

    return [participants.Participant(**m.to_dict()) for m in output]


def get_single_participant(
    participant_id,
) -> Optional[participants.Participant]:
    participant = db.collection("participants").document(participant_id).get()
    if not participant.exists:
        return None
    return participants.Participant(**participant.to_dict())


def get_many_participants(participant_ids: list) -> list:
    # Filter on the collection ids
    participants_list = (
        db.collection("participants")
        .where(FieldPath.document_id, "in", participant_ids)
        .stream()
    )
    return [participants.Participant(**m.to_dict()) for m in participants_list]


def insert_participant(
    participant: participants.Participant,
) -> participants.Participant:
    participant_inserted = db.collection("participants").insert(
        participant.model_dump()
    )
    return participants.Participant(**participant_inserted.to_dict())


def update_participant(participant: participants.Participant) -> None:
    db.collection("participants").document(participant.id).update(
        participant.model_dump()
    )


def patch_participant(participant_id: str, data: dict) -> None:
    db.collection("participants").document(participant_id).update(data)


def search_participants(search_term: str) -> list:
    filter_first_name = FieldFilter(
        "first_name", "==", str(search_term).upper()
    )
    filter_last_name = FieldFilter("last_name", "==", str(search_term).upper())
    filter_participant_email = FieldFilter("email", "==", search_term)

    or_filter = Or(
        filters=[filter_first_name, filter_last_name, filter_participant_email]
    )

    participants_list = (
        db.collection("participants").where(filter=or_filter).stream()
    )

    def ignore_error(c):
        try:
            return participants.Participant(**c.to_dict())
        except ValidationError:
            return None

    outputs = [
        participants.Participant(**m.to_dict()) for m in participants_list
    ]
    return [o for o in outputs if o is not None]
