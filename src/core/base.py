import logging
import typing as t

from src.core.config import get_settings
from src.db import db

logger = logging.Logger(__name__)

settings = get_settings()


class BaseService:
    collection_name: t.Optional[str] = None

    def __init__(self, *args, **kwargs):
        pass

    @property
    def collection(self) -> str:
        return self.collection_name or str(self.__class__.__name__)

    def get_items(self) -> t.List[t.Dict]:
        items = db.collection(self.collection).stream()
        return [item.to_dict() for item in items]

    def get_single_item(self, item_id) -> t.Dict:
        item = db.collection(self.collection).document(item_id).get()
        return item.to_dict()

    def create_item(self, item):
        db.collection(self.collection).add(item.dict())

    def update_item(self, item_id, item):
        db.collection(self.collection).document(item_id).update(item.dict())

    def delete_item(self, item_id):
        db.collection(self.collection).document(item_id).delete()
