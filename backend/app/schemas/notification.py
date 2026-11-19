"""
BankFlow AI - Notification Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class NotificationItem(BaseModel):
    """Schema for customer notification."""
    id: int
    customer_id: int
    request_id: Optional[int] = None
    notification_title: str
    notification_message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    """List of customer notifications and unread count."""
    items: List[NotificationItem]
    unread_count: int
    total: int
