"""
BankFlow AI - Messaging Customer Notification Dispatcher
Translates banking workflow events into customer-visible notifications.
Ensures customers only receive relevant updates for their own accounts and never internal agent chatter.
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.request import Request

logger = logging.getLogger("bankflow_ai.messaging.notifications")


def dispatch_customer_notification(
    db: Session,
    request: Request,
    title: str,
    message: str,
) -> Optional[Notification]:
    """
    Creates an isolated customer notification record linked to the customer's account.
    """
    if not request.customer_id:
        return None

    try:
        notif = Notification(
            customer_id=request.customer_id,
            request_id=request.id,
            notification_title=title,
            notification_message=message,
            is_read=False,
        )
        db.add(notif)
        db.flush()
        logger.debug("Dispatched customer notification for customer %s on request %s", request.customer_id, request.request_id)
        return notif
    except Exception as e:
        logger.error("Failed to generate customer notification: %s", str(e))
        return None
