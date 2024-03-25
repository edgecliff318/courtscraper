from src.core.base import BaseService
from src.models import events


class EventsService(BaseService):
    collection_name = "events"
    serializer = events.Event
