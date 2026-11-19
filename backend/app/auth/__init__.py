"""
BankFlow AI - Authentication Package
Exports core security functions, JWT handlers, and role-based dependencies.
"""

from app.auth.security import (
    hash_password,
    verify_password,
    validate_password_strength,
    login_rate_limiter,
)
from app.auth.jwt_handler import (
    create_access_token,
    decode_access_token,
    revoke_token,
    is_token_revoked,
)
from app.auth.dependencies import (
    get_current_user,
    require_customer,
    require_bank_employee,
    require_supervisor,
    require_admin,
    require_roles,
)
from app.auth.encryption import (
    encrypt_field,
    decrypt_field,
    encrypt_payload_fields,
    decrypt_payload_fields,
    mask_sensitive_value,
    EncryptionError,
    DecryptionError,
)

__all__ = [
    "hash_password",
    "verify_password",
    "validate_password_strength",
    "login_rate_limiter",
    "create_access_token",
    "decode_access_token",
    "revoke_token",
    "is_token_revoked",
    "get_current_user",
    "require_customer",
    "require_bank_employee",
    "require_supervisor",
    "require_admin",
    "require_roles",
    "encrypt_field",
    "decrypt_field",
    "encrypt_payload_fields",
    "decrypt_payload_fields",
    "mask_sensitive_value",
    "EncryptionError",
    "DecryptionError",
]
