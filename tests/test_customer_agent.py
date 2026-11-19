"""
BankFlow AI - Customer Agent Tests
Tests synthetic request generation, schema parameters, and correction submission.
"""

import sys
import os
import pytest

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.models.request import ServiceType
from app.simulation.model import BankingSimulationModel
from app.agents.customer_agent import CustomerAgent


def test_customer_agent_generation_all_services():
    """Verify CustomerAgent generates payloads for all four banking services."""
    model = BankingSimulationModel()
    cust_agent = model.customer_agent

    # 1. Cheque Book
    cheque_req = cust_agent.generate_synthetic_request(ServiceType.CHEQUE_BOOK, is_valid=True)
    assert cheque_req["service_type"] == ServiceType.CHEQUE_BOOK
    assert cheque_req["payload"]["number_of_leaves"] in [25, 50, 100]
    assert cheque_req["payload"]["account_id"] is not None

    # 2. Debit Card Replacement
    card_req = cust_agent.generate_synthetic_request(ServiceType.DEBIT_CARD_REPLACEMENT, is_valid=True)
    assert card_req["service_type"] == ServiceType.DEBIT_CARD_REPLACEMENT
    assert card_req["payload"]["replacement_reason"] == "Damaged Card"

    # 3. Address Update
    addr_req = cust_agent.generate_synthetic_request(ServiceType.ADDRESS_UPDATE, is_valid=True)
    assert addr_req["service_type"] == ServiceType.ADDRESS_UPDATE
    assert addr_req["payload"]["city"] == "Metropolis"
    assert addr_req["payload"]["postal_code"] == "10001"

    # 4. Account Application
    app_req = cust_agent.generate_synthetic_request(ServiceType.ACCOUNT_APPLICATION, is_valid=True)
    assert app_req["service_type"] == ServiceType.ACCOUNT_APPLICATION
    assert "@" in app_req["payload"]["email"]
    assert app_req["payload"]["requested_account_type"] == "SAVINGS"


def test_customer_agent_invalid_payload_generation():
    """Verify CustomerAgent generates invalid payloads when requested for scenario testing."""
    model = BankingSimulationModel()
    cust_agent = model.customer_agent

    invalid_cheque = cust_agent.generate_synthetic_request(ServiceType.CHEQUE_BOOK, is_valid=False)
    assert invalid_cheque["payload"]["number_of_leaves"] == 30  # Invalid leaves count
    assert invalid_cheque["payload"]["account_id"] is None


def test_customer_agent_correction_workflow():
    """Verify CustomerAgent receives correction notification and generates corrected payload."""
    model = BankingSimulationModel()
    cust_agent = model.customer_agent

    req_id = "BFA-REQ-TEST-CORR"
    cust_agent.receive_correction_notification(
        request_id=req_id,
        reason="Proof of Address Missing",
        instruction="Please provide clear address document.",
    )
    assert req_id in cust_agent.pending_corrections

    corrected_payload = cust_agent.generate_correction_payload(
        request_id=req_id,
        service_type=ServiceType.ADDRESS_UPDATE,
        account_id=5,
    )
    assert corrected_payload["account_id"] == 5
    assert corrected_payload["city"] == "Metropolis"
    assert req_id not in cust_agent.pending_corrections
