from datetime import datetime
from typing import Any

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    holiday_id: int | None
    flight_entry_id: int | None
    type: str
    title: str
    body: str
    extra: dict[str, Any] | None
    read_at: datetime | None
    email_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class UnreadCountResponse(BaseModel):
    unread: int
