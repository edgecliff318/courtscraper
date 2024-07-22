import logging
import typing as t
from datetime import datetime

from google.cloud.firestore_v1 import aggregation
from google.cloud.firestore_v1.base_query import And, FieldFilter, Or
from google.cloud.firestore_v1.field_path import FieldPath
from pydantic import BaseModel

from src.core.config import get_settings
from src.db import db

logger = logging.Logger(__name__)

settings = get_settings()


class BaseService:
    collection_name: str
    serializer: t.Type[BaseModel] = BaseModel

    def __init__(self, *args, **kwargs):
        pass

    @property
    def collection(self) -> str:
        return self.collection_name or str(self.__class__.__name__)

    def parse_filters(self, kwargs):
        filters = []
        for key, value in kwargs.items():
            if value is not None:
                if key == "id":
                    if isinstance(value, str):
                        filters.append(
                            FieldFilter(
                                FieldPath.document_id(),
                                "==",
                                db.document(f"{self.collection_name}/{value}"),
                            )
                        )
                    else:
                        filters.append(
                            FieldFilter(
                                FieldPath.document_id(),
                                "in",
                                [
                                    db.document(f"{self.collection_name}/{v}")
                                    for v in value
                                ],
                            )
                        )
                elif isinstance(value, list):
                    filters.append(FieldFilter(key, "in", value))
                elif "start" in key and isinstance(value, datetime):
                    filters.append(
                        FieldFilter(key.replace("start_", ""), ">=", value)
                    )
                elif "end" in key and isinstance(value, datetime):
                    filters.append(
                        FieldFilter(key.replace("end_", ""), "<=", value)
                    )
                else:
                    filters.append(FieldFilter(key, "==", value))

        filters = And(filters=filters)
        return filters

    def get_dict(self, item):
        output = item.to_dict()
        try:
            output.pop("id")
        except KeyError:
            pass
        return output

    def get_items(self, **kwargs) -> t.List[serializer]:
        if not kwargs:
            items = db.collection(self.collection).stream()
            return [
                self.serializer(**self.get_dict(item), id=item.id)
                for item in items
            ]

        items = (
            db.collection(self.collection)
            .where(filter=self.parse_filters(kwargs))
            .stream()
        )
        return [
            self.serializer(**self.get_dict(item), id=item.id)
            for item in items
        ]

    def get_single_item(self, item_id) -> serializer:
        item = db.collection(self.collection).document(item_id).get()

        if not item.exists:
            return None
        return self.serializer(**self.get_dict(item), id=item.id)

    def create_item(self, item):
        creation_date, reference = db.collection(self.collection).add(
            item.model_dump()
        )
        return reference

    def update_item(self, item_id, item):
        db.collection(self.collection).document(item_id).update(
            **item.model_dump()
        )

    def set_item(self, item_id, item):
        if isinstance(item, dict):
            db.collection(self.collection).document(item_id).set(item)
        else:
            db.collection(self.collection).document(item_id).set(
                item.model_dump()
            )

    def patch_item(self, item_id, data):
        db.collection(self.collection).document(item_id).update(data)

    def delete_item(self, item_id):
        db.collection(self.collection).document(item_id).delete()

    def search_items(self, search_term, search_columns):
        field_filters = []
        for column in search_columns:
            field_filters.append(FieldFilter(column, "==", search_term))

        or_filter = Or(filters=field_filters)

        items = (
            db.collection(self.collection).where(filters=or_filter).stream()
        )

        return [
            self.serializer(**self.get_dict(item), id=item.id)
            for item in items
        ]

    def count_items(self, filters=None, **kwargs):
        filters = filters or self.parse_filters(kwargs)
        query = db.collection(self.collection).where(filter=filters)
        aggregate_query = aggregation.AggregationQuery(query)
        outputs = aggregate_query.count(alias="count").get()

        for output in outputs:
            return output[0].value

        return None
