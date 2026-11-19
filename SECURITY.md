# BankFlow AI – Security Architecture & Data Protection Guide (Phase 7)

## 1. Overview
BankFlow AI operates as an educational and enterprise simulation platform demonstrating intelligent multi-agent banking workflows. Phase 7 introduces comprehensive security hardening across credential storage, sensitive data encryption at rest, 4-tier Role-Based Access Control (RBAC), API defense-in-depth middleware, tamper-resistant audit logging with automated credential sanitization, and secure inter-agent AMQP communication.

---

## 2. Password Security Architecture
- **Argon2id Hashing**: All user passwords (both Customer and Bank Staff accounts) are hashed using the state-of-the-art Argon2id algorithm via `pwdlib` and `argon2-cffi`. Argon2id provides maximum resilience against GPU/ASIC brute-force and side-channel timing attacks.
- **Complexity Validation**: Enforces minimum length (8+ characters) with uppercase, lowercase, numeric, and special character requirements.
- **Zero Plaintext Exposure**: Passwords are never stored in plaintext, never emitted in API responses (excluded via Pydantic model configurations), never logged in audit trails, and excluded from frontend state.
- **Distinct Authentication Realms**: Strict segregation between Customer authentication (`/api/auth/customer/*`) and Bank Staff authentication (`/api/auth/bank/*`).

---

## 3. Sensitive Data Encryption (AES-256-GCM)
Sensitive synthetic banking details (e.g., account numbers, residential addresses, document identity numbers, and credit details) are encrypted at the application boundary prior to database persistence.

- **Algorithm**: Authenticated AES-256-GCM (Galois/Counter Mode) via Python's standard `cryptography` library.
- **Authentication & Integrity**: Every encrypted ciphertext includes an authenticated tag and a 12-byte cryptographically secure random nonce (`os.urandom(12)`).
- **Tamper Resistance**: Any tampering with the ciphertext, tag, or nonce results in a `DecryptionError` and safe fallback handling rather than corrupting database transactions or raising unhandled 500 exceptions.
- **Format Prefix**: Encrypted strings are stored with the prefix `enc:v1:<base64-payload>`, enabling deterministic encryption detection, backward compatibility, and future key rotation support.
- **Key Derivation & Management**: Encryption keys are loaded from the `DATA_ENCRYPTION_KEY` environment variable. If a raw string is supplied, it is deterministically hashed using SHA-256 into a strict 32-byte (256-bit) key. Encryption keys are never hardcoded in source code or committed to version control.

---

## 4. Role-Based Access Control (RBAC)
BankFlow AI enforces a 4-tier role hierarchy:

| Role | Scope | Permitted Endpoints & Capabilities |
| :--- | :--- | :--- |
| **CUSTOMER** | Customer Portal | Access own accounts, view personal profile, submit service requests, review/correct own requests. Blocked from all employee, supervisor, admin, simulation, and messaging endpoints. |
| **BANK_EMPLOYEE** | Staff Operations | Search, filter, inspect customer service requests, manage human review queue, approve/reject/escalate requests. Blocked from customer accounts, admin role modification, and system encryption key rotation. |
| **SUPERVISOR** | Operations & Monitoring | All Bank Employee operational privileges, plus access to real-time multi-agent simulation status, agent pool metrics, telemetry dashboards, and RabbitMQ dead-letter queues. |
| **ADMINISTRATOR** | Full Management | Complete system oversight, user role reassignment (`PUT /api/bank/admin/users/{user_id}/role`), audit log inspection, and security posture monitoring (`GET /api/bank/admin/security-status`). |

### Authorization Boundaries
- **Ownership Verification**: Customers can only inspect their own requests (`Request.customer_id == current_user.id`). Attempting to fetch or update another customer's request raises `HTTP 403 Forbidden` or `HTTP 404 Not Found`.
- **Privilege Separation**: Employees cannot submit requests as customers; customers cannot access bank routes (`HTTP 403 Forbidden`).
- **Self-Escalation Prevention**: Users cannot alter their own roles or privileges; role changes require an authenticated `ADMINISTRATOR` token.

---

## 5. API Security & Defense-in-Depth Middleware
- **JWT Token Verification**: Stateless JWT tokens signed with HS256, strictly validated for signature integrity and expiration (`exp`). Token revocations on logout are immediately blacklisted in-memory/cache.
- **Request Body Size Limits**: Custom middleware rejects payloads exceeding `MAX_REQUEST_BODY_SIZE_BYTES` (default 2 MB / 2,097,152 bytes) with `HTTP 413 Payload Too Large`.
- **Defensive HTTP Security Headers**: Injected into every HTTP response:
  - `X-Content-Type-Options: nosniff` (prevents MIME type sniffing)
  - `X-Frame-Options: DENY` (clickjacking protection)
  - `X-XSS-Protection: 1; mode=block` (browser XSS filtering)
  - `Referrer-Policy: strict-origin-when-cross-origin` (prevents leakage of sensitive referral URIs)
- **Safe Error Handling**: Internal server errors do not expose internal stack traces, DB connection strings, or system paths to clients.

---

## 6. Audit Logging & Credential Sanitization
- **Structured Audit Trails**: Key business and security events (logins, failed logins, logouts, request submissions, human reviews, role changes, and sensitive data access) generate structured records:
  - `event_id`: Unique tracking UUID
  - `user_id`: Authenticated user ID (or null for anonymous failed attempts)
  - `request_id`: Associated banking request ID (if applicable)
  - `action`: Standardized event code (e.g., `USER_LOGIN_SUCCESS`, `SENSITIVE_DATA_ACCESS`, `ADMIN_ROLE_UPDATED`)
  - `outcome`: `SUCCESS`, `FAILURE`, or `DENIED`
  - `source_ip`: Originating client IP address
  - `description`: Sanitized contextual details
- **Automated Redaction Policy**: `AuditService.sanitize_description` uses regex pattern matching to automatically replace passwords, JWT tokens, Bearer authorization headers, encryption keys, and password hashes with `[REDACTED_BY_SECURITY_POLICY]`.

---

## 7. Inter-Agent Communication Security (RabbitMQ)
- **Credential Segregation**: Broker credentials (`RABBITMQ_USER`, `RABBITMQ_PASSWORD`, `RABBITMQ_HOST`, `RABBITMQ_PORT`, `RABBITMQ_VHOST`) are strictly loaded from environment configuration.
- **Payload Schema Validation**: All inter-agent messages are strictly validated by `StandardBankingMessage` schemas before broker dispatch. Payloads containing credentials (`password`, `token`, `secret`, `api_key`) are actively rejected before publishing.
- **Dead-Letter Isolation**: Poison pills and unparseable messages are moved to the isolated `bankflow.deadletter.q` without interrupting primary consumer pipelines.

---

## 8. Frontend Security Hardening
- **Session Expiration Event Dispatch**: The frontend API client detects `HTTP 401 Unauthorized` responses and immediately fires a global `bankflow:auth_expired` window event.
- **Clean State Teardown**: `AuthContext` clears authentication tokens, user state, and redirects the client to the appropriate login page.
- **Role-Based Navigation & UI Rendering**: Navigation tabs and administrative controls (e.g., `AdminManagementTab`) are dynamically rendered according to role hierarchy, preventing unauthorized UI actions.

---

## 9. Environment Configuration & Deployment Guidelines
Copy `backend/.env.example` to `backend/.env` and configure appropriate production secrets:

```env
# Critical Security Keys (Generate using: openssl rand -hex 32)
JWT_SECRET_KEY=generate-a-strong-random-secret-key-for-jwt-in-production
DATA_ENCRYPTION_KEY=generate-a-strong-32-byte-hex-key-for-aes-256-gcm-data-encryption

# Database & Broker
DATABASE_URL=postgresql://bankflow_user:secure_password@localhost:5432/bankflow_ai
RABBITMQ_USER=bankflow
RABBITMQ_PASSWORD=secure_broker_password
```

### Production Hardening Recommendations:
1. **Enforce HTTPS / TLS**: Terminate TLS at a reverse proxy (Nginx / Caddy / Cloudflare) using TLS 1.3. Set `Secure` and `HttpOnly` flags on authentication cookies.
2. **Restrict Broker Access**: Ensure RabbitMQ port `5672` is accessible only to backend services and not exposed to the public internet.
3. **Database Security**: Enforce SSL connections (`sslmode=require`) between backend and PostgreSQL database servers.
4. **Key Management Systems**: In cloud deployments (GCP/AWS/Azure), inject `DATA_ENCRYPTION_KEY` and `JWT_SECRET_KEY` from Secret Manager / HashiCorp Vault.

---

## 10. Automated Security Testing & Verification
A dedicated automated security test suite verifies all Phase 7 hardening measures:

```bash
# Run the complete test suite (129 tests across all phases)
cd BankFlow-AI
python -m pytest -v

# Run dedicated Phase 7 security tests
python -m pytest tests/test_security_hardening.py -v
```

### Verified Test Scenarios:
1. `test_customer_cannot_access_another_customer_profile`: Isolation between customer accounts.
2. `test_customer_cannot_access_another_customer_service_request`: Requests forbidden across different owners.
3. `test_employee_cannot_access_admin_endpoints`: Bank employee blocked from admin role assignments.
4. `test_supervisor_can_access_permitted_monitoring_endpoints`: Supervisor role permissions verified.
5. `test_invalid_or_expired_jwt_tokens_rejected`: Rejection of malformed, tampered, or expired tokens.
6. `test_incorrect_passwords_rejected`: Authentication failure on invalid credentials.
7. `test_passwords_never_stored_in_plaintext_and_argon2id_enforced`: Argon2id format and zero plaintext verification.
8. `test_aes_256_gcm_encryption_and_decryption_accuracy`: High-fidelity encryption and decryption cycle.
9. `test_modified_ciphertext_and_wrong_key_cause_safe_failures`: Tamper and bad-key rejection without uncaught crashes.
10. `test_unauthorized_users_cannot_modify_roles`: RBAC boundary on role modification.
11. `test_audit_logs_created_for_important_actions`: Audit trail creation across user actions.
12. `test_audit_logs_do_not_contain_passwords_or_tokens`: Automated redaction policy verification.
13. `test_malformed_rabbitmq_messages_rejected_safely`: AMQP message integrity and rejection of sensitive credentials.
14. `test_request_size_limit_and_security_headers`: HTTP 413 and defensive headers verification.
