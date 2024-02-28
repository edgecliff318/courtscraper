from src.core.base import BaseService
from src.models import flows


class FlowsService(BaseService):
    collection_name = "flows"
    serializer = flows.Flow
