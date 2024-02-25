from src.core.base import BaseService
from src.models import custom_fields


class CustomerCustomFieldsService(BaseService):
    collection_name = "tasks"
    serializer = custom_fields.CustomerCustomFields
