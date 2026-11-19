"""
BankFlow AI - Multi-Agent Communication & Coordination Tests
Tests complete end-to-end event exchange workflow across all 5 agent roles:
Customer -> Intake -> Request -> Verification -> Service -> Supervisor.
"""

import sys
import os
import pytest
from sqlalchemy.orm import Session

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.models.request import Request, ServiceType, RequestStatus
from app.models.agent_event import AgentEvent
from app.models.notification import Notification
from app.simulation.model import BankingSimulationModel
from app.messaging.queues import declare_queues_and_bindings
from app.messaging.broker_service import BrokerService


def test_end_to_end_agent_communication_flow(db_session: Session, sample_customer_and_account):
    """
    Validates complete cooperative multi-agent event exchange sequence:
    1. CustomerAgent generates & publishes REQUEST_CREATED.
    2. IntakeAgent receives, classifies, and publishes REQUEST_CLASSIFIED.
    3. RequestAgent accepts, queues, and publishes REQUEST_ACCEPTED.
    4. VerificationAgent verifies and publishes VERIFICATION_COMPLETED.
    5. ServiceAgent executes fulfillment and publishes SERVICE_COMPLETED.
    6. Customer receives milestone notifications.
    7. All exchanged events are queryable via BrokerService timeline.
    """
    declare_queues_and_bindings()
    customer, account = sample_customer_and_account
    model = BankingSimulationModel()

    req_id = "BFA-FLOW-2026-9001"
    req = Request(
        request_id=req_id,
        customer_id=customer.id,
        account_id=account.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.NEW,
        assignment_version=0,
        payload={"account_id": account.id, "number_of_leaves": 50},
    )
    db_session.add(req)
    db_session.flush()

    # Step 1: Customer Agent emits REQUEST_CREATED
    cust_msg = model.customer_agent.publish_request_created(db_session, req)
    assert cust_msg.event_type.value == "REQUEST_CREATED"

    # Step 2: Intake Agent validates & classifies request
    intake_res = model.intake_agent.process_request(db_session, req)
    assert intake_res.request_status == RequestStatus.CLASSIFIED

    # Step 3: Request Agent accepts assignment
    worker = model.get_request_agents()[0]
    worker.accept_and_queue_request(db_session, req)
    assert req.request_status == RequestStatus.QUEUED
    assert worker.current_request_id == req_id

    # Step 4: Verification Agent checks prerequisites
    verif_res = model.verification_agent.process_request(db_session, req)
    assert verif_res.request_status == RequestStatus.VERIFIED

    # Step 5: Service Agent executes fulfillment
    service_agent = model.get_service_agents()[0]  # Cheque book service agent
    completed_req = service_agent.execute_service(db_session, req)
    assert completed_req.request_status == RequestStatus.COMPLETED

    # Step 6: Verify communication timeline in PostgreSQL via BrokerService
    timeline = BrokerService.get_request_communication_timeline(db_session, req_id)
    assert len(timeline) >= 5

    event_types = [ev["event_type"] for ev in timeline]
    assert "REQUEST_CREATED" in event_types
    assert "REQUEST_CLASSIFIED" in event_types
    assert "REQUEST_ASSIGNED" in event_types
    assert "REQUEST_ACCEPTED" in event_types
    assert "VERIFICATION_COMPLETED" in event_types
    assert "SERVICE_STARTED" in event_types
    assert "SERVICE_COMPLETED" in event_types

    # Step 7: Verify customer notifications generated
    notifications = (
        db_session.query(Notification)
        .filter(Notification.customer_id == customer.id)
        .all()
    )
    assert len(notifications) >= 2  # Created + Completed notifications


def test_supervisor_heartbeat_and_alert_emission(db_session: Session):
    """Verify worker heartbeat emission and supervisor alert broadcast."""
    declare_queues_and_bindings()
    model = BankingSimulationModel()
    worker = model.get_request_agents()[0]

    # Worker emits heartbeat
    hb_msg = worker.emit_heartbeat(db_session)
    assert hb_msg.event_type.value == "AGENT_HEARTBEAT"
    assert hb_msg.sender_agent_id == "RequestAgent_1"

    # Supervisor broadcasts alert
    alert_msg = model.supervisor_agent.publish_alert(
        db=db_session,
        alert_type="HIGH_QUEUE_DEPTH",
        message_text="Verification queue exceeded 50 pending items.",
        details={"queue": "bankflow.verification.q", "depth": 52},
    )
    assert alert_msg.event_type.value == "SUPERVISOR_ALERT"
    assert alert_msg.reason_code == "HIGH_QUEUE_DEPTH"
