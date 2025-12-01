# app/schemas/notification.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: str
    title: str
    message: str
    link: Optional[str]
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
