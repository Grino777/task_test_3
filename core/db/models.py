from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class User(BaseModel):
    id: int
    created_at: datetime
    status: str
    status_updated_at: datetime
    last_message_sent_at: Optional[datetime] = None