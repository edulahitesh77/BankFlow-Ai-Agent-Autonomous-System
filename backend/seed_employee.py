"""
BankFlow AI - Development Bank Employee Seed Script
Provisions or updates a seed bank employee account using environment variables.
Run this script to initialize staff accounts for testing and evaluation.
Usage:
    python seed_employee.py
"""

import sys
import os

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.config import settings
from app.database import SessionLocal
from app.services.user_service import UserService


def seed_bank_employee():
    """Seed or update development bank employee account."""
    print("=" * 60)
    print("BankFlow AI - Bank Employee Provisioning Utility")
    print("=" * 60)

    db = SessionLocal()
    try:
        user, employee = UserService.provision_bank_employee(
            db=db,
            username=settings.SEED_EMPLOYEE_USERNAME,
            email=settings.SEED_EMPLOYEE_EMAIL,
            password=settings.SEED_EMPLOYEE_PASSWORD,
            employee_code=settings.SEED_EMPLOYEE_CODE,
            full_name=settings.SEED_EMPLOYEE_NAME,
            department=settings.SEED_EMPLOYEE_DEPARTMENT,
            designation=settings.SEED_EMPLOYEE_DESIGNATION,
            branch_id=settings.SEED_EMPLOYEE_BRANCH,
        )

        print("[SUCCESS] Bank employee account provisioned:")
        print(f"  - Employee Code : {employee.employee_code}")
        print(f"  - Username      : {user.username}")
        print(f"  - Full Name     : {employee.full_name}")
        print(f"  - Email         : {user.email}")
        print(f"  - Role          : {user.role.value}")
        print(f"  - Department    : {employee.department}")
        print(f"  - Designation   : {employee.designation}")
        print(f"  - Branch ID     : {employee.branch_id}")
        print("  - Password      : [CONFIGURED IN .env]")
        print("=" * 60)

    except Exception as exc:
        print(f"[ERROR] Failed to seed bank employee: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed_bank_employee()
