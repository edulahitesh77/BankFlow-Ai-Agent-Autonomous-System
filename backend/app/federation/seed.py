"""
BankFlow AI - Multi-Branch Federation Seeding (Phase 10)
Provisions synthetic branch records, customers, accounts, employees, and agents
into their respective isolated branch databases.
"""

import hashlib
import logging
from sqlalchemy.orm import Session
from app.database import BranchDatabaseManager, SessionLocal
from app.models.branch import Branch, BranchStatus
from app.models.user import User, UserRole
from app.models.customer import Customer
from app.models.account import Account
from app.models.employee import Employee
from app.models.agent import Agent, AgentType, AgentHealthStatus
from app.auth.security import hash_password

logger = logging.getLogger("bankflow_ai.federation.seed")

BRANCH_METADATA = [
    {
        "branch_id": "BLR001",
        "branch_name": "Bengaluru",
        "location": "Bengaluru, Karnataka",
        "branch_status": "ACTIVE",
        "api_endpoint": "http://localhost:8000/api/branches/BLR001",
        "database_name": "bankflow_ai_blr",
        "secret": "blr_fed_key_2026_secret",
    },
    {
        "branch_id": "CHE001",
        "branch_name": "Chennai",
        "location": "Chennai, Tamil Nadu",
        "branch_status": "ACTIVE",
        "api_endpoint": "http://localhost:8000/api/branches/CHE001",
        "database_name": "bankflow_ai_che",
        "secret": "che_fed_key_2026_secret",
    },
    {
        "branch_id": "HYD001",
        "branch_name": "Hyderabad",
        "location": "Hyderabad, Telangana",
        "branch_status": "ACTIVE",
        "api_endpoint": "http://localhost:8000/api/branches/HYD001",
        "database_name": "bankflow_ai_hyd",
        "secret": "hyd_fed_key_2026_secret",
    },
]


def seed_all_branches(is_test: bool = False):
    """Provisions all three fictional branches with isolated synthetic data."""
    # 1. Seed Branch Directory in primary and branch databases
    for b_meta in BRANCH_METADATA:
        b_id = b_meta["branch_id"]
        session = BranchDatabaseManager.get_session(b_id, is_test=is_test)

        try:
            # Sync branch registry
            for entry in BRANCH_METADATA:
                existing_b = session.query(Branch).filter(Branch.branch_id == entry["branch_id"]).first()
                if not existing_b:
                    b_obj = Branch(
                        branch_id=entry["branch_id"],
                        branch_name=entry["branch_name"],
                        location=entry["location"],
                        branch_status=entry["branch_status"],
                        api_endpoint=entry["api_endpoint"],
                        database_name=entry["database_name"],
                        api_key_hash=hashlib.sha256(entry["secret"].encode("utf-8")).hexdigest(),
                        is_gateway_enabled=True,
                    )
                    session.add(b_obj)

            # 2. Seed Branch-Specific Synthetic Customer and Account
            cust_code = f"CUST-{b_id}-0001"
            acc_num = f"ACC-{b_id}-1001"
            username = f"{b_id.lower()}_customer_01"
            emp_code = f"EMP-{b_id}-0001"

            user = session.query(User).filter(User.username == username).first()
            if not user:
                user = User(
                    username=username,
                    email=f"customer@{b_id.lower()}.bankflow.synthetic",
                    password_hash=hash_password("BranchPass@2026!"),
                    role=UserRole.CUSTOMER,
                    is_active=True,
                )
                session.add(user)
                session.flush()

            cust = session.query(Customer).filter(Customer.customer_code == cust_code).first()
            if not cust:
                cust = Customer(
                    user_id=user.id,
                    customer_code=cust_code,
                    full_name=f"{b_meta['branch_name']} Customer",
                    email=user.email,
                    phone=f"+91-80-{b_id[-3:]}-0100",
                    branch_id=b_id,
                )
                session.add(cust)
                session.flush()

            acc = session.query(Account).filter(Account.synthetic_account_number == acc_num).first()
            if not acc:
                acc = Account(
                    customer_id=cust.id,
                    synthetic_account_number=acc_num,
                    account_type="SAVINGS",
                    account_status="ACTIVE",
                    branch_id=b_id,
                )
                session.add(acc)

            # 3. Seed Branch-Specific Employee
            emp_user = session.query(User).filter(User.username == f"{b_id.lower()}_officer").first()
            if not emp_user:
                emp_user = User(
                    username=f"{b_id.lower()}_officer",
                    email=f"officer@{b_id.lower()}.bankflow.synthetic",
                    password_hash=hash_password("OfficerPass@2026!"),
                    role=UserRole.BANK_EMPLOYEE,
                    is_active=True,
                )
                session.add(emp_user)
                session.flush()

            emp = session.query(Employee).filter(Employee.employee_code == emp_code).first()
            if not emp:
                emp = Employee(
                    user_id=emp_user.id,
                    employee_code=emp_code,
                    full_name=f"{b_meta['branch_name']} Lead Officer",
                    department="Branch Operations",
                    designation="Operations Manager",
                    branch_id=b_id,
                )
                session.add(emp)

            # 4. Seed Branch Agents
            agent_code = f"RequestAgent_{b_id}_1"
            agent = session.query(Agent).filter(Agent.agent_code == agent_code).first()
            if not agent:
                agent = Agent(
                    agent_code=agent_code,
                    agent_type=AgentType.REQUEST,
                    availability_status="AVAILABLE",
                    processing_status="IDLE",
                    health_status=AgentHealthStatus.HEALTHY,
                    branch_id=b_id,
                    completed_work_count=0,
                )
                session.add(agent)

            session.commit()
            logger.info("Successfully seeded branch '%s' (%s)", b_id, b_meta["branch_name"])

        except Exception as e:
            session.rollback()
            logger.error("Error seeding branch '%s': %s", b_id, str(e))
        finally:
            session.close()


if __name__ == "__main__":
    seed_all_branches()
    print("Multi-Branch synthetic data successfully provisioned across all branch databases!")
