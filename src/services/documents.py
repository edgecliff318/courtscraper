from src.core.base import BaseService
from src.models import documents


class DocumentsService(BaseService):
    collection_name = "documents"
    serializer = documents.Document
