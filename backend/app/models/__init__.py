"""
BankFlow AI - Database Models Package
Aggregates all SQLAlchemy models and enums for migration autogeneration and clean imports.
"""

from app.database import Base
from app.models.user import User, UserRole
from app.models.customer import Customer
from app.models.employee import Employee
from app.models.account import Account
from app.models.request import Request, ServiceType, RequestStatus
from app.models.agent import Agent, AgentType, AgentHealthStatus
from app.models.failure_record import AgentFailure, FailureType, RecoveryStatus
from app.models.audit_log import AuditLog
from app.models.review_record import ReviewRecord, ReviewDecision
from app.models.correction_record import CorrectionRecord
from app.models.notification import Notification
from app.models.processed_message import ProcessedMessage
from app.models.agent_event import AgentEvent
from app.models.delivery_attempt import MessageDeliveryAttempt
from app.models.branch import Branch, BranchStatus
from app.models.federation_event import FederationEvent

__all__ = [
    "Base",
    "User",
    "UserRole",
    "Customer",
    "Employee",
    "Account",
    "Request",
    "ServiceType",
    "RequestStatus",
    "Agent",
    "AgentType",
    "AgentHealthStatus",
    "AgentFailure",
    "FailureType",
    "RecoveryStatus",
    "AuditLog",
    "ReviewRecord",
    "ReviewDecision",
    "CorrectionRecord",
    "Notification",
    "ProcessedMessage",
    "AgentEvent",
    "MessageDeliveryAttempt",
    "Branch",
    "BranchStatus",
    "FederationEvent",
]
