from src.models import participants
from src.core.base import BaseService


class ParticipantsService(BaseService):
    collection_name = "participants"
    serializer = participants.Participant
