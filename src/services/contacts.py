from src.core.base import BaseService
from src.models import contacts


class ContactsService(BaseService):
    collection_name = "contacts"
    serializer = contacts.Contact
