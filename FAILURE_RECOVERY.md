# BankFlow AI – Advanced Agent Failure Recovery and Fault Tolerance (Phase 8)

## 1. Overview
BankFlow AI operates as a resilient, educational multi-agent banking system. Phase 8 introduces an autonomous self-healing and fault-tolerance architecture capable of detecting worker crashes, unresponsive heartbeats, task timeouts, broker unavailability, and duplicate message delivery without losing state or generating duplicate request fulfillments.

PostgreSQL remains the authoritative source of truth for request registry and agent assignments, while RabbitMQ coordinates resilient, non-blocking inter-agent event delivery.

---

## 2. Agent Health States & Heartbeat Architecture

### A. Health States
Each agent tracks six distinct operational and health states:

| Health State | Semantics | Work Eligibility |
| :--- | :--- | :--- |
| **`HEALTHY`** | Agent is operational, heartbeats are fresh, ready for assignment. | Eligible |
| **`IDLE`** | Operational and waiting for new tasks. | Eligible |
| **`BUSY`** | Actively processing a bound request version. | Ineligible for new assignments |
| **`UNRESPONSIVE`** | Missed periodic heartbeat threshold (> 15s). | Ineligible; tasks subject to recovery |
| **`FAILED`** | Suffered an execution crash, OOM, or unhandled exception. | Ineligible; tasks subject to recovery |
| **`RECOVERING`** | Task released; agent undergoing reset or cooldown. | Ineligible until restored |

### B. Heartbeat Mechanism
- **Cadence**: Healthy agents periodically emit heartbeats (default `AGENT_HEARTBEAT_INTERVAL_SECONDS = 5.0`).
- **Timeout Threshold**: Configurable threshold (default `AGENT_HEARTBEAT_TIMEOUT_SECONDS = 15.0`). If `now - last_heartbeat_at > 15s`, the agent transitions to `UNRESPONSIVE`.
- **Database Persistence**: Heartbeat timestamps and latencies are synced to the PostgreSQL `agents` table (`last_heartbeat_at`, `total_processing_time_ms`, `failed_work_count`).

---

## 3. Failure Detection Scenarios

The system automatically detects eight failure conditions:

1. **Missed Heartbeats**: Worker stops sending heartbeats (`UNRESPONSIVE_HEARTBEAT`).
2. **Process / Execution Crashes**: Worker throws unhandled exceptions or crashes during task steps (`CRASH_DURING_EXECUTION`).
3. **Processing Timeouts**: Request remains assigned to an agent exceeding the SLA timeout (`PROCESSING_TIMEOUT`, default 30s).
4. **Broker Unavailability**: Connection to RabbitMQ fails or trips the circuit breaker (`RABBITMQ_UNAVAILABLE`, `DEPENDENCY_CIRCUIT_OPEN`).
5. **Duplicate Deliveries**: Redelivered or replayed messages detected via idempotency registries (`DUPLICATE_DELIVERY`).
6. **Repeated Processing Failures**: Request fails repeatedly across retry attempts (`REPEATED_PROCESSING_FAILURE`).
7. **Invalid / Incomplete Result Payloads**: Worker sends malformed result data (`INVALID_RESULT_PAYLOAD`).
8. **Stale Processing Attempts**: Delayed or zombie agents attempt to fulfill tasks whose assignment version has progressed.

For every failure, an immutable record is registered in `agent_failures`:
- `failure_id`: Unique identifier (e.g., `FAIL-ABCD1234EF`)
- `agent_code`: Associated agent
- `request_code`: Associated request
- `failure_type`: Enumerated failure category
- `error_details`: Sanitized error description (credentials and internal traces stripped)
- `recovery_status`: `DETECTED`, `RECOVERING`, `RECOVERED`, `FAILED`, or `ESCALATED_TO_HUMAN`

---

## 4. Automatic Request Recovery Workflow

When an agent fails or becomes unresponsive while holding an active request:

```
[Agent Becomes Unresponsive or Crashes]
                │
                ▼
   [Atomic Concurrency Lock on Request]
                │
                ├──> If already terminal (COMPLETED/REJECTED) -> Abort (Preserve Finality)
                │
                ▼
   [Retry Eligibility Check (RecoveryRetryService)]
                │
       ┌────────┴────────┐
       ▼                 ▼
[Quota Exceeded    [Quota Available &
or Permanent Error] Retryable Error]
       │                 │
       │                 ▼
       │         [Increment Request assignment_version (+1)]
       │         [Increment Request retry_count (+1)]
       │         [Unbind Failed Agent (current_request_id = None)]
       │                 │
       ▼                 ▼
[Escalate to       [Search for Healthy, Idle Replacement Agent]
 HUMAN_REVIEW]           │
                   ┌─────┴─────┐
                   ▼           ▼
          [Replacement    [No Idle Agent
             Found]          Available]
                   │           │
                   ▼           ▼
          [Bind New Agent] [Queue Request in
          [Publish Alert]   QUEUED State]
                   │           │
                   └─────┬─────┘
                         ▼
             [Record in AuditLog Table]
             [Update FailureRecord -> RECOVERED]
```

### Assignment Versioning & Anti-Zombie Protection
- Every request maintains `assignment_version`.
- When recovery reallocates a request, `assignment_version` increments.
- If a stale agent wakes up after network partition and calls `complete_and_release`, it is strictly rejected (`self.assigned_version < request.assignment_version`).

---

## 5. Retry Policy & Exponential Backoff

- **Max Retries**: Default `RECOVERY_MAX_RETRIES = 3`.
- **Initial Delay**: Default `RECOVERY_INITIAL_RETRY_DELAY_SECONDS = 2.0`.
- **Backoff Factor**: Default `RECOVERY_BACKOFF_FACTOR = 2.0`.
- **Schedule**:
  - Attempt 1: 2.0s
  - Attempt 2: 4.0s
  - Attempt 3: 8.0s
  - Maximum Delay Cap: 30.0s
- **Classification**:
  - *Retryable*: Timeouts, worker crashes, connection blips, transient locks.
  - *Non-Retryable*: Invalid form fields (e.g., cheque leaves != 25/50/100), closed accounts, ownership mismatches.
- **Retry Exhaustion**: When the retry limit is reached, the request transitions to `HUMAN_REVIEW` with `review_required = True`. Requests are never silently discarded or rejected simply because a worker failed.

---

## 6. Circuit Breaker for External Dependencies

Protects against cascading failures when external services (e.g. RabbitMQ) encounter disruptions:

- **States**:
  - `CLOSED`: Normal traffic passed through.
  - `OPEN`: Failure threshold exceeded (default 3 consecutive errors); requests fail fast with `CircuitBreakerOpenException` and messages remain safely queued in DB outbox.
  - `HALF_OPEN`: Recovery timeout elapsed (default 10s); allows canary trial requests to probe dependency health.
- **Transitions**:
  - `CLOSED -> OPEN`: Consecutive failures >= threshold.
  - `OPEN -> HALF_OPEN`: Recovery timeout expired.
  - `HALF_OPEN -> CLOSED`: Canary requests succeed.
  - `HALF_OPEN -> OPEN`: Canary request fails.

---

## 7. Customer & Employee Experience

### Customer Facing
- Request status remains accurate (`QUEUED`, `IN_SERVICE`, `HUMAN_REVIEW`).
- If retries occur (`retry_count > 0`), the UI displays:
  > *"Your request is taking longer than expected. Our team is monitoring it."*
- Technical stack traces, error codes, and agent failures are completely hidden.

### Employee & Supervisor Facing
- Dedicated **Recovery & Reliability** dashboard (`/bank/dashboard` -> Recovery tab).
- Displays real-time KPI cards: Total Agents, Healthy, Busy, Unresponsive, Failed, Recovered Tasks, Human Review.
- Interactive controls:
  - *Inspect Health*: Force on-demand heartbeat verification.
  - *Manual Retry*: Retry failed requests.
  - *Manual Reassign*: Force reassignment to a specific healthy worker.
  - *Reset Agent Health*: Return an agent back to `HEALTHY`.
  - *Pause / Resume Agent*: Administratively control worker availability.
  - *Reset Circuit Breaker*: Manually close tripped circuit breakers.

---

## 8. Failure Simulation & Chaos Testing Panel

Available in development/testing via `/api/bank/recovery/simulation/*` or the dashboard UI:

1. **Simulate Agent Crash**: `POST /api/bank/recovery/simulation/crash` with `{ "agent_code": "RequestAgent_1" }`.
2. **Simulate Missed Heartbeat**: `POST /api/bank/recovery/simulation/missed-heartbeat` with `{ "agent_code": "RequestAgent_2", "seconds_ago": 60 }`.
3. **Simulate RabbitMQ Outage**: `POST /api/bank/recovery/simulation/rabbitmq-outage` trips circuit breaker to `OPEN`.
4. **Restore RabbitMQ**: `POST /api/bank/recovery/simulation/rabbitmq-restore` resets circuit breaker to `CLOSED`.
5. **Simulate Retry Exhaustion**: `POST /api/bank/recovery/simulation/exhaust-retries/{request_id}` verifies escalation to `HUMAN_REVIEW`.

---

## 9. Verification & Testing Commands

```bash
# Run all automated tests (145 tests across all phases)
cd BankFlow-AI
python -m pytest -v

# Run Phase 8 Failure Recovery tests only (16 tests)
python -m pytest tests/test_failure_recovery.py -v

# Run Frontend Production Build
cd BankFlow-AI/frontend
npm run build
```

---

## 10. Known Limitations
- In-memory Mesa agent state is synchronized on discrete simulation ticks; database persistence remains the authoritative lock.
- RabbitMQ circuit breaker fail-fast currently defaults outbox persistence directly to PostgreSQL until the broker re-establishes connectivity.
- Branch federation and Unity 2D visual integration are deferred to future project phases.
