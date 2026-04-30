from datetime import datetime

from pydantic import BaseModel


class ShareTokenResponse(BaseModel):
    token: str
    url: str
    revoked_at: datetime | None
    expires_at: datetime | None
    created_at: datetime
