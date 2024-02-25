from src.core.base import BaseService
from src.models import billings


class BillingsService(BaseService):
    collection_name = "billings"
    serializer = billings.Billing
