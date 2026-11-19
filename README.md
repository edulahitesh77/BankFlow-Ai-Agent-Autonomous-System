# BankFlow AI – Intelligent Multi-Agent Banking Service Automation System

**Phases 1–10: Dual Authentication, Customer Portal, Bank Management, Supervisory Review, Multi-Agent Swarm, Structured Message Broker, Security Hardening, Agent Failure Recovery & Fault Tolerance, Unity 2D Multi-Agent Visualization Dashboard, and Multi-Branch Federation & Cloud Architecture**

BankFlow AI is an educational banking service automation system simulating an intelligent multi-agent banking operations architecture. This project demonstrates how cooperative AI agents communicate, process, verify, route, and resolve synthetic customer service requests with auditability, strict role boundaries, message durability, data encryption at rest, automated fault recovery, real-time 2D multi-agent visualization, and sovereign multi-branch federation.

> **Important Notice**: This project uses only synthetic banking data. It does not connect to real financial institutions or perform real monetary transactions. Account application pre-screenings and review completion events record simulated staff concurrence, not real-world banking credit underwriting or account opening.

---

## 1. Technologies Used

- **Backend Language & Runtime**: Python 3.12+
- **Web Framework**: FastAPI (v0.115+)
- **Message Broker & Event-Driven Architecture**: RabbitMQ 4.0.5, `pika` (v1.3+), `aio-pika` (v10.2+)
- **Multi-Agent Modeling**: Mesa (v3.1+) Agent-Based Modeling framework
- **2D Visualization & Replay Dashboard**: Unity (2022.3 LTS / Unity 6), C#, uGUI, TextMeshPro, UnityWebRequest
- **Fault Tolerance & Reliability**: Circuit Breaker Pattern, Exponential Backoff, Idempotency Registry, Atomic Task Reassignment
- **Cryptography & Security**: AES-256-GCM (`cryptography` v50.0+), Argon2id (`argon2-cffi`), PyJWT (`pyjwt`)
- **ASGI Server**: Uvicorn
- **Database**: PostgreSQL 18
- **ORM**: SQLAlchemy (v2.0+)
- **Migrations**: Alembic (v1.14+)
- **Data Validation & Settings**: Pydantic v2 & Pydantic Settings
- **Frontend Stack**: React 18, Vite, Tailwind CSS, Lucide React, React Router v6
- **Testing**: Pytest (168 automated tests, 100% pass rate), Pytest-Asyncio, HTTPX
- **Federation & Cloud**: Multi-Branch Sovereign PostgreSQL, HMAC SHA-256 Gateway, Docker Compose Microservices
- **Performance Evaluation**: Repeatable Scenarios P1–P5 benchmark suite (Workloads 10–100, Agent Pools 1–8)
- **API Documentation**: FastAPI Swagger UI (`/docs`) & ReDoc (`/redoc`)

---

## 2. Project Folder Structure

```
BankFlow-AI/
│
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI application setup, CORS, lifespan, router registry
│   │   ├── database.py              # SQLAlchemy engine, session maker & get_db dependency
│   │   ├── config.py                # Pydantic Settings configuration from .env & environment
│   │   │
│   │   ├── auth/                    # Authentication & security module
│   │   │   ├── __init__.py          # Security exports
│   │   │   ├── security.py          # Argon2id password hashing & rate limiter
│   │   │   ├── encryption.py        # Phase 7: AES-256-GCM field encryption & credential masking
│   │   │   ├── jwt_handler.py       # JWT creation, decoding & server-side token revocation
│   │   │   └── dependencies.py      # get_current_user, require_customer, require_bank_employee, require_supervisor, require_admin
│   │   │
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   │   ├── __init__.py          # Model exports
│   │   │   ├── user.py              # User authentication credentials & 4-tier roles
│   │   │   ├── customer.py          # Customer profile & synthetic code
│   │   │   ├── employee.py          # Bank employee credentials & staff code
│   │   │   ├── account.py           # Synthetic customer bank accounts
│   │   │   ├── request.py           # Customer banking service requests
│   │   │   ├── agent.py             # Multi-agent registry & availability
│   │   │   ├── failure_record.py    # Phase 8: Agent failure records & recovery status
│   │   │   ├── audit_log.py         # Compliance audit log records with security tracking
│   │   │   ├── review_record.py     # Staff review notes & escalation records
│   │   │   ├── correction_record.py # Customer correction history
│   │   │   ├── notification.py      # Customer status notifications
│   │   │   ├── agent_event.py       # Phase 6: Exchanged broker communication audit events
│   │   │   ├── processed_message.py # Phase 6: Idempotency registry for consumed messages
│   │   │   └── delivery_attempt.py  # Phase 6: Per-attempt tracking, duplicates & retries
│   │   │
│   │   ├── messaging/               # Phase 6: RabbitMQ Structured Messaging Engine
│   │   │   ├── __init__.py          # Messaging exports
│   │   │   ├── connection.py        # RabbitMQConnectionManager (Pika & aio-pika singleton)
│   │   │   ├── circuit_breaker.py   # Phase 8: External dependency circuit breaker (CLOSED, OPEN, HALF_OPEN)
│   │   │   ├── routing.py           # Exchanges, Queues, and Topic Routing Key bindings
│   │   │   ├── exchanges.py         # Durable topic exchanges (bankflow.events, bankflow.dlx)
│   │   │   ├── queues.py            # Durable agent queues with DLX policies & status
│   │   │   ├── message_schema.py    # StandardBankingMessage Pydantic schema & credential filter
│   │   │   ├── publisher.py         # MessagePublisher with Transactional Outbox pattern & circuit protection
│   │   │   ├── consumer.py          # MessageConsumer with manual ack & version checks
│   │   │   ├── duplicate_protection.py # Idempotency service via ProcessedMessages
│   │   │   ├── retry.py             # RetryPolicyService (max 3 retries -> DLX routing)
│   │   │   ├── dead_letter.py       # Dead-letter inspection and authorized staff replay
│   │   │   ├── notifications.py     # In-app customer notification dispatcher
│   │   │   └── broker_service.py    # Queue depth, broker health & timeline service
│   │   │
│   │   ├── agents/                  # Phase 5: Mesa Multi-Agent Swarm
│   │   │   ├── __init__.py          # Agent role exports
│   │   │   ├── base_agent.py        # BaseBankingAgent extending mesa.Agent with heartbeat & health states
│   │   │   ├── customer_agent.py    # CustomerAgent (synthetic generation & corrections)
│   │   │   ├── intake_agent.py      # IntakeAgent (validation & classification)
│   │   │   ├── request_agent.py     # RequestAgent (single-request worker & version guard)
│   │   │   ├── verification_agent.py# VerificationAgent (prerequisites & account checks)
│   │   │   ├── service_agent.py     # ServiceAgent (skill-matched fulfillment)
│   │   │   └── supervisor_agent.py  # SupervisorAgent (telemetry, heartbeat inspection & recovery)
│   │   │
│   │   ├── simulation/              # Phase 5: Discrete-Tick Simulation Core
│   │   │   ├── __init__.py          # Simulation exports
│   │   │   ├── configuration.py     # SimulationConfig dataclass
│   │   │   ├── state_machine.py     # Lifecycle state machine & transition validator
│   │   │   ├── scheduler.py         # WorkloadScheduler & LeastLoadedPolicy
│   │   │   ├── agent_registry.py    # AgentRegistry sync with PostgreSQL
│   │   │   ├── model.py             # BankingSimulationModel (mesa.Model)
│   │   │   └── simulation_runner.py # Thread-safe runner & scenarios 1-5 benchmarks
│   │   │
│   │   ├── schemas/                 # Pydantic validation schemas
│   │   │   ├── user.py              # Customer registration & login schemas
│   │   │   ├── customer.py          # Customer dashboard, accounts & requests
│   │   │   ├── bank.py              # Bank employee dashboard & request management
│   │   │   ├── admin.py             # Phase 7: Administrator user management & security schemas
│   │   │   ├── recovery.py          # Phase 8: Health summaries, failure logs & reassignment schemas
│   │   │   ├── agent_simulation.py  # Swarm telemetry, controls & scenario benchmarks
│   │   │   └── messaging.py         # Phase 6: Broker health, queue status, event items & timeline schemas
│   │   │
│   │   ├── routes/                  # API routers
│   │   │   ├── auth.py              # Customer & employee authentication routes
│   │   │   ├── customer.py          # Customer banking dashboard endpoints
│   │   │   ├── bank.py              # Bank management & supervisory review endpoints
│   │   │   ├── admin.py             # Phase 7: Administrator user roles & security status endpoints
│   │   │   ├── recovery.py          # Phase 8: Failure recovery, manual retry & chaos simulation APIs
│   │   │   ├── agents.py            # Multi-agent swarm inspection & metrics
│   │   │   ├── simulation.py        # Simulation engine controls & scenario runs
│   │   │   └── messaging.py         # Phase 6: RabbitMQ inspection, events & dead-letter APIs
│   │   │
│   │   └── services/                # Business logic services
│   │       ├── user_service.py      # User registration, verification & profiles
│   │       ├── customer_service.py  # Customer accounts & service request processing
│   │       ├── bank_service.py      # Supervisory review, metrics & corrections
│   │       ├── audit_service.py     # Phase 7: Automated credential sanitization & audit event recording
│   │       ├── recovery_service.py  # Phase 8: Autonomous heartbeat inspection & atomic request recovery
│   │       ├── retry_service.py     # Phase 8: Exponential backoff & retry classification
│   │       ├── failure_simulation_service.py # Phase 8: Chaos testing & failure injection harness
│   │       └── agent_service.py     # Agent introspection & scenario benchmarks
│   │
│   ├── alembic/                     # Database migrations
│   │   └── versions/                # Version migration scripts
│   ├── requirements.txt             # Pinned backend dependencies
│   ├── docker-compose.yml           # Phase 6: RabbitMQ & PostgreSQL container orchestration
│   ├── SECURITY.md                  # Phase 7: Security architecture & data protection guide
│   ├── FAILURE_RECOVERY.md          # Phase 8: Advanced failure recovery & fault tolerance architecture
│   └── alembic.ini                  # Alembic environment configuration
│
├── frontend/                        # React 18 + Vite frontend
│   ├── src/
│   │   ├── api/auth.js              # Comprehensive REST API client with auto 401 expiration dispatch
│   │   ├── pages/
│   │   │   ├── auth/                # Customer and Bank Employee Login / Register
│   │   │   ├── customer/            # Customer Portal (Dashboard, Accounts, Requests)
│   │   │   └── bank/                # Bank Employee & Administrator Portal
│   │   │       ├── BankDashboard.jsx# Main administration container
│   │   │       └── components/      # Tab components (Requests, Review, Monitoring, Messaging, Admin, Recovery)
│   │   │           ├── AgentMonitoringTab.jsx    # Live Swarm Monitor & Scenario Runner
│   │   │           ├── AgentCommunicationTab.jsx # Phase 6: Broker Queues, Event Feeds & DLQ Replay
│   │   │           ├── AdminManagementTab.jsx    # Phase 7: Role Management & Security Architecture Status
│   │   │           └── AgentRecoveryTab.jsx      # Phase 8: Health KPIs, Failure Logs & Chaos Simulation
│   │   ├── components/common/       # Reusable UI components & modals
│   │   └── App.jsx                  # Route configuration & protected route wrappers
│   ├── package.json
│   └── vite.config.js
│
└── tests/                           # Complete automated pytest test suite (145 tests)
    ├── conftest.py                  # Pytest fixtures and test database sessions
    ├── test_database.py             # Phase 1: Models and database relations
    ├── test_auth.py                 # Phase 2: Dual authentication and RBAC
    ├── test_customer_dashboard.py   # Phase 3: Customer requests and accounts
    ├── test_bank_dashboard.py       # Phase 4: Bank dashboard, review and audit
    ├── test_customer_agent.py       # Phase 5: Customer agent generation & correction
    ├── test_intake_agent.py         # Phase 5: Intake validation and classification
    ├── test_request_agent.py        # Phase 5: RequestAgent pool and concurrency
    ├── test_verification_agent.py   # Phase 5: Verification prerequisites & ownership
    ├── test_service_agent.py        # Phase 5: Skill compatibility and fulfillment
    ├── test_supervisor_agent.py     # Phase 5: Telemetry and health metrics
    ├── test_simulation.py           # Phase 5: State machine, scenarios 1-5, and APIs
    ├── test_messaging_schema.py     # Phase 6: StandardBankingMessage schema & sensitive filtering
    ├── test_message_broker.py       # Phase 6: RabbitMQ connection, queue inspection & manual ack
    ├── test_duplicate_protection.py # Phase 6: Idempotent message deduplication
    ├── test_message_retry.py        # Phase 6: Retry policy, backoff & dead letter replay
    ├── test_request_consistency.py  # Phase 6: Single-request ownership & state versioning
    ├── test_agent_communication.py  # Phase 6: End-to-end agent event coordination flow
    ├── test_messaging_api.py        # Phase 6: Bank messaging inspection & timeline REST APIs
    ├── test_security_hardening.py   # Phase 7: AES-256-GCM, RBAC boundaries, headers & sanitization
    └── test_failure_recovery.py     # Phase 8: Heartbeat timeouts, atomic reassignment, circuit breaker, chaos testing
```

---

## 3. Phase 5: Multi-Agent System Architecture

Phase 5 introduces an auditable Multi-Agent System using the **Mesa 3.x** Agent-Based Modeling library integrated with PostgreSQL persistence.

### Core Agent Roles

1. **Customer Agent (`CustomerAgent`)**:
   - Generates realistic synthetic customer request payloads across all 4 service categories (`CHEQUE_BOOK`, `DEBIT_CARD_REPLACEMENT`, `ADDRESS_UPDATE`, `ACCOUNT_APPLICATION`).
   - Supports customer resubmission workflows when requests are returned with status `NEEDS_CORRECTION`.

2. **Intake Agent (`IntakeAgent`)**:
   - Performs syntactic validation and completeness checks on incoming requests in state `NEW`.
   - Transitions requests to `CLASSIFIED`, `NEEDS_CORRECTION` (missing fields), `HUMAN_REVIEW` (lost debit card replacements), or `REJECTED_INPUT`.

3. **Verification Agent (`VerificationAgent`)**:
   - Cross-references synthetic account numbers, active account statuses, and customer ownership records.
   - Detects account ownership mismatches (`REJECTED_INPUT`).
   - Routes new account applications to `HUMAN_REVIEW` for simulated staff KYC concurrence.

4. **Request Agent Pool (`RequestAgent`)**:
   - Pool of configurable worker instances (`RequestAgent_1`, `RequestAgent_2`, `RequestAgent_3`, etc.).
   - Enforces **single-request exclusive ownership** (an agent can hold at most one active request).
   - Manages monotonic version tracking (`assignment_version`).

5. **Service Agent Pool (`ServiceAgent`)**:
   - Skill-compatible execution agents (`ServiceAgent_CHEQUE_BOOK`, `ServiceAgent_DEBIT_CARD`, `ServiceAgent_ADDRESS`, `ServiceAgent_APPLICATION`).
   - Executes simulated fulfillment tasks, appends dispatch metadata, and transitions requests to `COMPLETED`.

6. **Supervisor Agent (`SupervisorAgent`)**:
   - Monitors multi-agent health telemetry, active worker counts, system load ratios, and detects workflow bottlenecks.

### Strict State Machine Lifecycle

State transitions follow an explicit, rule-based transition matrix defined in `app/simulation/state_machine.py`:

```
NEW ───► CLASSIFIED ───► QUEUED ───► VERIFIED ───► IN_SERVICE ───► COMPLETED
 │            │             │            │              │
 ├──► NEEDS_CORRECTION ◄────┴────────────┴──────────────┘
 │            │ (Customer Resubmits)
 │            ▼
 ├──► NEW (Resubmitted with incremented version)
 │
 ├──► HUMAN_REVIEW ───► VERIFIED (Staff Approves)
 │         │
 │         └──► REJECTED_INPUT (Staff Rejects)
 │
 └──► REJECTED_INPUT (Terminal invalid state)
```

- **Duplicate Completion Protection**: Requests in terminal state `COMPLETED` cannot transition to any other state (`DuplicateCompletionError`).
- **Audit Trails**: Every state transition automatically creates an immutable `AuditLog` entry detailing agent code, timestamps, and reason codes.

### Controlled Benchmark Scenarios (1 to 5)

Phase 5 includes 5 deterministic simulation scenarios accessible via API and Bank Dashboard UI:

- **Scenario 1: Normal Processing**: 20 valid requests processed by 3 Request Agents to full completion.
- **Scenario 2: Increased Load Stress Test**: 60 valid requests processed by 5 Request Agents demonstrating concurrency distribution.
- **Scenario 3: Incomplete Requests**: 20 requests (50% missing required fields) demonstrating automatic routing to `NEEDS_CORRECTION`.
- **Scenario 4: Mixed Service Types**: 24 requests evenly distributed across all 4 service types.
- **Scenario 5: Human Review Gate**: 20 requests combining lost card replacements and account applications routed to `HUMAN_REVIEW`.

---

## 4. API Endpoints Reference

### Multi-Agent & Simulation Endpoints (Internal Bank Staff Only)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/bank/agents` | Lists all registered agents and their availability status |
| `GET` | `/api/bank/agents/statistics` | Retrieves aggregated swarm telemetry |
| `GET` | `/api/bank/agents/{agent_id}` | Retrieves details for an individual agent |
| `GET` | `/api/bank/agents/communication` | Phase 6: Messages published and tasks consumed per agent |
| `GET` | `/api/bank/simulation/status` | Returns current simulation running status and active ticks |
| `GET` | `/api/bank/simulation/statistics` | Returns simulation pipeline volume and backlog counts |
| `POST` | `/api/bank/simulation/start` | Starts the background discrete-tick simulation engine |
| `POST` | `/api/bank/simulation/stop` | Stops the background simulation engine |
| `POST` | `/api/bank/simulation/run-test` | Executes a benchmark scenario (1 through 5) |

### Phase 6: RabbitMQ Messaging & Broker Inspection Endpoints (Internal Bank Staff Only)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/bank/messaging/status` | Retrieves RabbitMQ broker connectivity and exchange topology |
| `GET` | `/api/bank/messaging/queues` | Retrieves queue depths, message counts, and consumer counts |
| `GET` | `/api/bank/messaging/statistics` | Aggregate message volume, duplicate catches, and retry metrics |
| `GET` | `/api/bank/messaging/events` | Paginated event history filtered by request ID, agent ID, or event type |
| `GET` | `/api/bank/messaging/events/{request_id}` | Chronological message exchange timeline for an individual request |
| `GET` | `/api/bank/messaging/dead-letter` | Inspects failed messages currently in `bankflow.dlq` |
| `POST` | `/api/bank/messaging/retry/{message_id}` | Authorized bank staff action to replay dead-lettered message |

---

## 5. Phase 6: Structured Multi-Agent Communication Architecture

### RabbitMQ Topology
- **Main Exchange**: `bankflow.events` (Topic, Durable)
- **Dead-Letter Exchange**: `bankflow.dlx` (Topic, Durable)
- **Queues**:
  - `bankflow.intake.q` (Bindings: `request.created`, `request.corrected`)
  - `bankflow.request_agent.q` (Binding: `request.classified`)
  - `bankflow.verification.q` (Binding: `request.assigned`)
  - `bankflow.service.q` (Binding: `verification.completed`)
  - `bankflow.supervisor.q` (Bindings: `agent.heartbeat.*`, `request.human_review.*`, `request.correction_needed.*`)
  - `bankflow.notification.q` (Bindings: `request.created`, `verification.completed`, `service.completed`, `request.human_review.*`, `request.correction_needed.*`)
  - `bankflow.dlq` (Binding: `#` from `bankflow.dlx`)

### Reliability & Consistency Guarantees
1. **Transactional Outbox & Audit**: Every published event is logged to the PostgreSQL `agent_events` table within the database transaction before or concurrently with AMQP delivery.
2. **Standard Message Schema**: Pydantic-validated `StandardBankingMessage` schema with strict rejection of malformed envelopes or forbidden sensitive credentials (`password`, `jwt_token`, `pin`, `pan`, `cvv`).
3. **Manual Acknowledgement**: Consumers explicitly `basic_ack` only upon successful handler execution and database commit; exceptions trigger controlled `basic_nack(requeue=False)` routing to DLX.
4. **Idempotency & Duplicate Protection**: PostgreSQL `processed_messages` table ensures duplicate messages are detected and safely discarded without re-executing business logic.
5. **Exponential Backoff & DLQ**: Failed messages are retried up to 3 times before dead-lettering into `bankflow.dlq`.
6. **State & Version Consistency**: Consumers verify request versions against PostgreSQL to reject stale messages, and enforce single-worker exclusive ownership.

---

## 6. Automated Test Suite (115 Passing Tests)

Run the full pytest suite with:

```powershell
cd BankFlow-AI
python -m pytest tests/ -v
```

All **115 automated tests** pass across 19 test modules:

1. **`tests/test_messaging_schema.py` (5 tests)**:
   - Valid standard message envelope validation.
   - Missing required field rejection.
   - Unknown event type rejection.
   - Negative request version rejection.
   - Forbidden sensitive credential filtering (passwords, PINs, tokens).
2. **`tests/test_message_broker.py` (3 tests)**:
   - RabbitMQ connection health and status inspection.
   - Exchange and durable queue topology declaration.
   - Persistent message publishing and manual ack consumption.
3. **`tests/test_duplicate_protection.py` (2 tests)**:
   - Duplicate message identification and suppression via `ProcessedMessages`.
   - Consumer idempotency preventing duplicate handler execution.
4. **`tests/test_message_retry.py` (3 tests)**:
   - Transient failure retry count logging.
   - Max 3 retries threshold routing to dead-letter queue (`bankflow.dlq`).
   - Authorized bank staff dead letter replay and reprocessing.
5. **`tests/test_request_consistency.py` (3 tests)**:
   - RequestAgent single-request exclusive ownership enforcement.
   - Stale request version detection and rejection.
   - Duplicate request completion protection.
6. **`tests/test_agent_communication.py` (2 tests)**:
   - End-to-end multi-agent message routing from Customer Agent -> Intake -> Request Agent -> Verification -> Service Agent.
   - Supervisor heartbeat tracking and alert emission.
7. **`tests/test_messaging_api.py` (7 tests)**:
   - Broker status endpoint (`/api/bank/messaging/status`).
   - Queue depth endpoint (`/api/bank/messaging/queues`).
   - Communication statistics endpoint (`/api/bank/messaging/statistics`).
   - Exchanged event history and per-request chronological timeline endpoints.
   - Dead-letter queue listing and replay endpoints.
   - Agent communication metrics endpoint (`/api/bank/agents/communication`).
   - Role-based access control preventing customer access to messaging APIs.
8. **`tests/test_simulation.py` (12 tests)**:
   - Lifecycle state transitions and audit logging.
   - Invalid state transition prevention.
   - Duplicate completion protection.
   - Concurrency distribution across Request Agents.
   - Benchmark Scenarios 1, 3, and 5.
   - Agent and simulation REST APIs and RBAC enforcement.
9. **`tests/test_customer_agent.py` (3 tests)**:
   - Synthetic request generation across all 4 services.
   - Incomplete payload generation.
   - Correction resubmission workflow.
10. **`tests/test_intake_agent.py` (4 tests)**:
    - Cheque book request classification.
    - Leaf selection validation and `NEEDS_CORRECTION`.
    - Security card replacement human review referral.
    - Address completeness validation.
11. **`tests/test_verification_agent.py` (3 tests)**:
    - Active account prerequisite verification.
    - Account application referral to `HUMAN_REVIEW`.
    - Account ownership mismatch rejection.
12. **`tests/test_request_agent.py` (3 tests)**:
    - RequestAgent pool initialization.
    - Single-request exclusive ownership enforcement.
    - Task completion and worker release.
13. **`tests/test_service_agent.py` (3 tests)**:
    - Skill-based request acceptance.
    - Unverified request rejection.
    - Fulfillment execution and simulated dispatch metadata.
14. **`tests/test_supervisor_agent.py` (3 tests)**:
    - Operational health report generation.
    - System load ratio calculation with active workers.
15. **`tests/test_bank_dashboard.py` (13 tests)**:
    - Real database metric aggregations, search, and filtering.
    - Human review approval, rejection, and escalation workflows.
    - Request correction workflows and customer directory.
16. **`tests/test_customer_dashboard.py` (14 tests)**:
    - Customer dashboard metrics, synthetic accounts, and 4 service forms.
    - Data isolation and request correction resubmissions.
17. **`tests/test_auth.py` (20 tests)**:
    - Argon2id password hashing and complexity validation.
    - Customer and employee authentication, JWT tokens, and revocation.
18. **`tests/test_database.py` (12 tests)**:
    - PostgreSQL connectivity, tables, and relationships.
19. **`tests/test_security_hardening.py` (14 tests)**:
    - Customer profile and service request cross-tenant data isolation.
    - Role-based boundaries (employees blocked from admin endpoints, supervisors permitted monitoring).
    - JWT token signature and expiration rejection.
    - Password authentication, Argon2id enforcement, and zero plaintext exposure.
    - AES-256-GCM encryption accuracy, random nonces, and corrupted ciphertext handling.
    - User self-role escalation prevention.
    - Audit log generation for critical events and regex sanitization of credentials.
    - Malformed and credential-bearing RabbitMQ message rejections.
    - HTTP 413 maximum payload size limit and defensive HTTP security headers.
20. **`tests/test_failure_recovery.py` (16 tests)**:
    - Agent heartbeat emission and freshness timestamp tracking.
    - Unresponsive agent detection after missed heartbeat timeout.
    - Automatic request recovery, version incrementing, and reallocation to healthy Request Agent.
    - Stale worker anti-zombie protection (older assignment versions strictly cannot complete reassigned requests).
    - Mathematical precision of exponential backoff delays (2s, 4s, 8s capped at 30s).
    - Retry limit exhaustion escalating tasks to `HUMAN_REVIEW` without data loss or premature rejection.
    - Deterministic non-retryable error classification (e.g. invalid leaves, closed accounts).
    - Circuit breaker state transitions (`CLOSED` -> `OPEN` -> `HALF_OPEN` -> `CLOSED`).
    - Circuit breaker fail-fast rejections when `OPEN`.
    - Concurrency competition: atomic single-ownership guarantees.
    - Duplicate message deduplication preventing repeated task execution.
    - Staff supervisor recovery endpoints (`retry`, `reassign`, `reset`, `pause/resume`).
    - Customer RBAC isolation (customers forbidden with `HTTP 403` on all recovery endpoints).
    - Customer reassurance messaging on delayed requests without technical error exposure.
    - Audit log persistence across all automated and manual recovery events.
21. **`tests/test_unity_export.py` (9 tests)**:
    - Pydantic schema validation for `SimulationManifestExport` (strict `schema_version == "1.0.0"`).
    - 8-stage workflow status mappings (`STAGE_1_CUSTOMER` through `STAGE_8_FINISHED`).
    - Deterministic multi-tick benchmark replay generation with timeout and supervisor failover events.
    - Atomic file output guarantees using `.tmp` write and atomic replace.
    - Live database state extraction and agent telemetry mapping.
    - FastAPI manifest, snapshot, and atomic export endpoint validation.
    - Role-based access control protecting simulation endpoints from unauthorized access (`HTTP 403`).
22. **`tests/test_federation.py` (11 tests)**:
    - F1: Bengaluru to Chennai authorized cross-branch account status confirmation.
    - F2: Bengaluru to Hyderabad authorized customer KYC verification.
    - F3: Rejection of invalid/unauthorized branch service credentials (`401 Unauthorized`).
    - F4: Rejection of out-of-scope information queries (`403 Forbidden`).
    - F5: Anti-replay enforcement rejecting duplicate UUID correlation IDs (`409 Conflict`).
    - F6: Graceful fallback and error reporting when destination branch database is offline.
    - REST endpoint tests for `/api/federation/exchange`, `/branches`, `/statistics`, and `/events`.
    - Customer RBAC isolation forbidding non-staff users from accessing federation gateways (`HTTP 403`).
23. **`tests/test_performance_evaluator.py` (3 tests)**:
    - Lightweight process CPU and memory resource sampling validation.
    - Single-run benchmark execution computing throughput, latency, and agent utilization metrics.
    - CSV and JSON experimental export integrity and summary statistics verification.

---

## 4. Phase 7: Security Hardening & Data Protection Architecture

BankFlow AI implements enterprise-grade security hardening across all layers:
- **Argon2id Hashing**: Credentials verified using state-of-the-art Argon2id hashing algorithms.
- **AES-256-GCM Field Encryption**: Sensitive synthetic banking fields encrypted at the application boundary prior to database storage, using 256-bit keys and 12-byte random nonces.
- **4-Tier RBAC**: `CUSTOMER`, `BANK_EMPLOYEE`, `SUPERVISOR`, and `ADMINISTRATOR` roles with strict route dependencies.
- **Defensive HTTP Middleware**: Security headers (`X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`) and a 2 MB request body limit returning `HTTP 413`.
- **Sanitized Audit Logging**: Real-time redaction policy replacing passwords, tokens, Bearer headers, and secrets with `[REDACTED_BY_SECURITY_POLICY]`.
- **Frontend Security Integration**: Session expiration listener on `HTTP 401` dispatching `bankflow:auth_expired`, with dedicated `AdminManagementTab` for administrators.

---

## 5. Phase 8: Agent Failure Recovery & Fault Tolerance Architecture

Phase 8 equips the BankFlow AI system with an autonomous self-healing operational layer:
- **6-State Health Registry**: `HEALTHY`, `IDLE`, `BUSY`, `UNRESPONSIVE`, `FAILED`, and `RECOVERING` tracking heartbeats, retries, and task execution latencies.
- **Atomic Concurrency & Version Guarding**: Every reassignment increments `assignment_version`. Late/zombie worker completions are strictly rejected by version checks.
- **Exponential Backoff Retry Engine**: Automatic retries using formula `initial_delay * (2 ^ (attempt - 1))` (2s, 4s, 8s) up to 3 attempts, with non-retryable business failure classification.
- **Human Review Escalation**: Requests exceeding retry limits escalate to `HUMAN_REVIEW` with full audit logs and notifications; requests are never silently discarded.
- **Circuit Breaker for Broker Disruptions**: Stateful `CLOSED`, `OPEN`, and `HALF_OPEN` protection for RabbitMQ, preventing cascade thread blocking and ensuring database outbox durability.
- **Supervisor Recovery Dashboard**: Real-time health metrics, recent failure records, and interactive controls to inspect heartbeats, retry tasks, reassign workers, and reset circuit breakers.
- **Chaos Engineering Harness**: Administrative controls to simulate crashes, stale heartbeats, broker outages, and retry exhaustion for continuous resilience validation.

---

## 6. Phase 9: Unity 2D Multi-Agent Visualization Dashboard Architecture

Phase 9 implements an interactive 2D visualization and replay dashboard built with Unity (2022.3 LTS / Unity 6):
- **Authoritative Separation**: Python and Mesa remain the authoritative source of truth for simulation execution, database records, and performance metrics. Unity acts purely as the client-side visualization and replay layer.
- **Strict Data Contract**: Simulation manifests adhere to `schema_version: "1.0.0"`. File writes use atomic `.tmp` replacement to prevent corrupted or partial file reads.
- **Two Visualization Modes**:
  - **Mode 1: Recorded Replay**: Deterministic playback of benchmark scenarios (`sample_simulation.json`) with Play, Pause, Step Forward/Back, Timeline scrubbing, and Speed control ($0.5\times$ to $5.0\times$) without mutating the PostgreSQL database.
  - **Mode 2: Live Monitoring**: Real-time REST polling of FastAPI endpoints (`/api/bank/simulation/snapshot`) reflecting live database states and active agent queues.
- **8-Stage Workflow Visualizer**:
  - Visual layout spanning Stage 1 (Customer) $\to$ Stage 2 (Intake) $\to$ Stage 3 (Assignment) $\to$ Stage 4 (Verification) $\to$ Stage 5 (Service Execution) $\to$ Stage 6 (Correction) $\to$ Stage 7 (Human Review) $\to$ Stage 8 (Finished).
  - Color-coded request tokens with smooth lerp positioning and interactive click drill-down.
- **Dynamic Multi-Agent Swarm**:
  - Supports $N$ concurrent Request Agents alongside Customer, Intake, Verification, Service, and Supervisor agents.
  - Real-time health status badges: `HEALTHY` (green), `BUSY` (cyan), `IDLE` (slate), `UNRESPONSIVE` (amber), `FAILED` (red), `RECOVERING` (orange).
  - Glowing message trajectories and arrival pulse animations.
- **Supervisor & Recovery Panel**:
  - Real-time supervisor heartbeat indicator, failure detection counters, and automated task reassignment tracking.
  - Interactive Event Inspection panel for reviewing immutable audit histories of requests and agents.
- **Setup & Demonstration Guide**: Complete step-by-step instructions and presentation scripts are available in [`UNITY_SETUP.md`](UNITY_SETUP.md).

---

## 7. Phase 10: Multi-Branch Federation & Cloud Architecture

Phase 10 extends BankFlow AI with a decentralized multi-branch federation architecture and containerized cloud deployment:
- **Three Sovereign Bank Branches**:
  - **Bengaluru Branch** (`BLR001` - Karnataka, `bankflow_ai_blr`)
  - **Chennai Branch** (`CHE001` - Tamil Nadu, `bankflow_ai_che`)
  - **Hyderabad Branch** (`HYD001` - Telangana, `bankflow_ai_hyd`)
- **Strict Sovereign Database Isolation**: Each branch maintains its own dedicated PostgreSQL database. Branches never directly query other branches' tables.
- **Central Federation Gateway**:
  - Authenticates branch requests using constant-time HMAC SHA-256 with pre-shared secrets.
  - Enforces three authorized least-privilege scopes: `ACCOUNT_STATUS_CONFIRMATION`, `CUSTOMER_KYC_VERIFICATION`, and `SERVICE_ELIGIBILITY_CONFIRMATION`.
  - Sanitizes returned payloads to strip sensitive account numbers, balances, credentials, and internal keys.
  - Enforces anti-replay protection using globally unique correlation IDs.
  - Inscribes dual-branch audit log entries in both source and destination branch databases.
- **Branch Federation Dashboard Tab**: Bank staff can monitor branch health, active agents, cross-branch exchange volumes, success rates, and event streams directly from the web dashboard.
- **Unity Federation Visualization**: Interactive multi-branch topology view rendering active branch nodes, cross-branch query trajectories, and federation telemetry counters.
- **Cloud-Ready Container Architecture**:
  - Independent Docker containers for FastAPI API, Mesa background workers, PostgreSQL cluster, RabbitMQ broker, and Nginx React frontend.
  - Configurable via `docker-compose.yml` and automated multi-database initialization script (`docker/init-multi-db.sh`).

---

## 8. Repeatable Performance Evaluation Suite

BankFlow AI includes an automated benchmark evaluation runner (`simulation/performance_evaluator.py`) testing workloads from 10 to 100 requests across agent pools from 1 to 8 workers:
- **Scenario P1 (Concurrent Arrivals)**: Evaluates queuing and latency under burst request arrivals.
- **Scenario P2 (Agent Pool Scaling)**: Measures throughput speedup and agent idle % across 1, 2, 4, and 8 Request Agents.
- **Scenario P3 (Agent Failure & Recovery)**: Evaluates autonomous recovery time and atomic double-processing prevention under worker crashes.
- **Scenario P4 (Unequal Service Demand)**: Tests resilience under a heavy 70% Loan application workload.
- **Scenario P5 (Branch Federation)**: Measures inter-branch gateway exchange latency and federation throughput.

### Benchmark Results Summary
| Scenario | Workload | Pool Size | Total Time | Throughput | Avg Latency | Recovery Time | Fed Latency | Success Rate |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **P1** | 10 req | 4 agents | 5.85s | 102.6 req/min | 3.56s | - | - | 100% |
| **P1** | 20 req | 4 agents | 11.31s | 106.1 req/min | 6.65s | - | - | 100% |
| **P1** | 50 req | 4 agents | 27.08s | 110.8 req/min | 15.12s | - | - | 100% |
| **P1** | 100 req | 4 agents | 54.25s | 110.6 req/min | 30.16s | - | - | 100% |
| **P2** | 50 req | 1 agent | 29.35s | 102.2 req/min | 16.16s | - | - | 100% |
| **P2** | 50 req | 2 agents | 28.12s | 106.7 req/min | 15.82s | - | - | 100% |
| **P2** | 50 req | 4 agents | 26.91s | 111.5 req/min | 15.18s | - | - | 100% |
| **P2** | 50 req | 8 agents | 27.43s | 109.4 req/min | 15.77s | - | - | 100% |
| **P3** | 20 req | 4 agents | 10.93s | 109.8 req/min | 6.40s | **0.0101s** | - | 100% |
| **P3** | 50 req | 4 agents | 27.83s | 107.8 req/min | 15.49s | **0.0455s** | - | 100% |
| **P4** | 20 req | 4 agents | 9.44s | 127.1 req/min | 5.49s | - | - | 100% |
| **P4** | 50 req | 4 agents | 22.20s | 135.1 req/min | 12.48s | - | - | 100% |
| **P5** | 20 req | 4 agents | 10.99s | 109.2 req/min | 6.51s | - | **152.96ms** | 100% |
| **P5** | 50 req | 4 agents | 27.49s | 109.1 req/min | 15.45s | - | **10.49ms** | 100% |

Results are exported to [`experiments/results.csv`](experiments/results.csv) and [`experiments/results.json`](experiments/results.json).

---

## 9. Comprehensive Documentation Index
- **Multi-Branch Federation**: [`FEDERATION_ARCHITECTURE.md`](FEDERATION_ARCHITECTURE.md)
- **Cloud & Container Deployment**: [`DEPLOYMENT.md`](DEPLOYMENT.md)
- **Empirical Performance Evaluation**: [`PERFORMANCE_EVALUATION.md`](PERFORMANCE_EVALUATION.md)
- **Unity 2D Visualization Setup & Demo**: [`UNITY_SETUP.md`](UNITY_SETUP.md)




