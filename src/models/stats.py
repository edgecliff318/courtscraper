from datetime import datetime

from pydantic import BaseModel


class Sales(BaseModel):
    customer_id: str
    date: datetime
    count: int = 0
    amount: float = 0.0
    details: dict | None = None
    outbound_actions_count: int = 0
    inbound_actions_count: int = 0
