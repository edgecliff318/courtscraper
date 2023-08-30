from datetime import datetime
from typing import Optional

from pydantic import BaseModel, validator


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    scope: str
    created: datetime = datetime.now()
    expires: datetime = datetime.now()
    id_token: Optional[str] = None
    user_id: Optional[str] = None
    id_token_jwt: Optional[str] = None
    token_response: Optional[dict] = None
    scopes: Optional[list] = None
