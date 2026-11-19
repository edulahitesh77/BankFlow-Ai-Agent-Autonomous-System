"""
BankFlow AI - Data Encryption Module
Provides AES-256-GCM authenticated encryption for sensitive synthetic banking data.
Implements unique per-operation nonces, secure key derivation, and tamper-evident authentication tags.
"""

import os
import base64
import hashlib
from typing import Optional, Dict, Any, List
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config import settings

ENCRYPTION_PREFIX = "enc:v1:"
NONCE_LENGTH = 12  # 96-bit standard nonce for AES-GCM
DEFAULT_SENSITIVE_KEYS = [
    "delivery_address",
    "street_address",
    "new_address",
    "annual_income",
    "tax_id",
    "tax_id_number",
    "id_number",
    "national_id",
    "document_reference",
    "phone_number",
    "account_number",
]


class EncryptionError(Exception):
    """Base exception for encryption failures."""
    pass


class DecryptionError(EncryptionError):
    """Raised when ciphertext authentication or decryption fails."""
    pass


def get_encryption_key(key_override: Optional[str] = None) -> bytes:
    """
    Derives a cryptographically secure 256-bit (32-byte) binary key.
    Accepts 64-character hex strings or derives via SHA-256 digest.
    """
    raw_key = key_override if key_override is not None else settings.DATA_ENCRYPTION_KEY
    if not raw_key:
        raise EncryptionError("DATA_ENCRYPTION_KEY is not configured.")

    if isinstance(raw_key, bytes):
        if len(raw_key) == 32:
            return raw_key
        return hashlib.sha256(raw_key).digest()

    raw_str = str(raw_key).strip()
    if len(raw_str) == 64:
        try:
            return bytes.fromhex(raw_str)
        except ValueError:
            pass

    # Fallback to SHA-256 key derivation to guarantee exactly 32 bytes
    return hashlib.sha256(raw_str.encode("utf-8")).digest()


def encrypt_field(
    plaintext: Optional[str],
    key: Optional[bytes] = None,
) -> Optional[str]:
    """
    Encrypts a plaintext string using AES-256-GCM with a fresh 12-byte random nonce.
    Returns formatted envelope: 'enc:v1:<base64(nonce + ciphertext + tag)>'.
    """
    if plaintext is None:
        return None
    if not isinstance(plaintext, str):
        plaintext = str(plaintext)

    k = key if key is not None else get_encryption_key()
    aesgcm = AESGCM(k)
    nonce = os.urandom(NONCE_LENGTH)

    try:
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        encoded = base64.b64encode(nonce + ciphertext).decode("ascii")
        return f"{ENCRYPTION_PREFIX}{encoded}"
    except Exception as exc:
        raise EncryptionError(f"Encryption failed: {str(exc)}") from exc


def decrypt_field(
    ciphertext: Optional[str],
    key: Optional[bytes] = None,
) -> Optional[str]:
    """
    Decrypts an AES-256-GCM envelope.
    If the string is unencrypted or empty, safely returns it as-is for backward compatibility.
    Raises DecryptionError if the ciphertext has been modified or the key is invalid.
    """
    if ciphertext is None:
        return None
    if not isinstance(ciphertext, str):
        return ciphertext

    # If not encrypted with our format, return plaintext as-is
    if not ciphertext.startswith(ENCRYPTION_PREFIX):
        return ciphertext

    k = key if key is not None else get_encryption_key()
    aesgcm = AESGCM(k)
    raw_b64 = ciphertext[len(ENCRYPTION_PREFIX):]

    try:
        combined = base64.b64decode(raw_b64, validate=True)
        if len(combined) < NONCE_LENGTH + 16:  # 12 bytes nonce + 16 bytes GCM tag
            raise DecryptionError("Ciphertext payload is too short to contain valid nonce and authentication tag.")

        nonce = combined[:NONCE_LENGTH]
        actual_ciphertext = combined[NONCE_LENGTH:]
        decrypted_bytes = aesgcm.decrypt(nonce, actual_ciphertext, None)
        return decrypted_bytes.decode("utf-8")
    except Exception as exc:
        raise DecryptionError(f"Decryption failed: corrupted ciphertext or invalid key. ({str(exc)})") from exc


def encrypt_payload_fields(
    payload: Optional[Dict[str, Any]],
    sensitive_keys: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Recursively encrypts sensitive fields in a dictionary before database persistence.
    """
    if payload is None:
        return None

    keys_to_encrypt = set(sensitive_keys or DEFAULT_SENSITIVE_KEYS)
    result = {}

    for k, v in payload.items():
        if k in keys_to_encrypt and isinstance(v, (str, int, float)):
            result[k] = encrypt_field(str(v))
        elif isinstance(v, dict):
            result[k] = encrypt_payload_fields(v, sensitive_keys)
        else:
            result[k] = v

    return result


def decrypt_payload_fields(
    payload: Optional[Dict[str, Any]],
    sensitive_keys: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Safely decrypts sensitive fields in a dictionary for authorized operations.
    """
    if payload is None:
        return None

    keys_to_decrypt = set(sensitive_keys or DEFAULT_SENSITIVE_KEYS)
    result = {}

    for k, v in payload.items():
        if k in keys_to_decrypt and isinstance(v, str) and v.startswith(ENCRYPTION_PREFIX):
            try:
                result[k] = decrypt_field(v)
            except DecryptionError:
                result[k] = "[ENCRYPTED_DATA_DECRYPTION_FAILED]"
        elif isinstance(v, dict):
            result[k] = decrypt_payload_fields(v, sensitive_keys)
        else:
            result[k] = v

    return result


def mask_sensitive_value(value: Optional[str], visible_chars: int = 4) -> str:
    """Masks a sensitive string value for safe display in logs or UI (e.g. '****-5678')."""
    if not value:
        return "—"
    clean = str(value).strip()
    if len(clean) <= visible_chars:
        return "*" * len(clean)
    return "*" * (len(clean) - visible_chars) + clean[-visible_chars:]
