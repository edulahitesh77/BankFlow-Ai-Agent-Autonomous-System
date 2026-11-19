# BankFlow AI – Cloud & Container Deployment Guide

## 1. Architecture Overview
BankFlow AI is architected as a set of decoupled, cloud-ready containerized microservices:
- **FastAPI Core & Gateway**: Exposes customer and employee REST APIs, rate limiters, auth middleware, and Federation Gateway routes.
- **Mesa Simulation Workers**: Asynchronous worker processes driving multi-agent simulations, health heartbeats, and workflow state transitions.
- **PostgreSQL Multi-Database Cluster**: High-availability database cluster hosting sovereign branch databases (`bankflow_ai_blr`, `bankflow_ai_che`, `bankflow_ai_hyd`) and main cluster registry (`bankflow_ai`).
- **RabbitMQ Message Broker**: Enterprise AMQP broker providing structured agent message exchanges, dead-letter routing, and durable queues.
- **React Frontend**: Optimized Single Page Application (SPA) served via Nginx with automated reverse proxying.
- **Unity Visualization Dashboard**: Standalone WebGL or native client for visual 2D simulation replay and telemetry monitoring.

```
                         [ Internet / Client Devices ]
                                      |
                             +--------v--------+
                             |   Nginx Ingress |
                             | (TLS Term, SPA) |
                             +---+----------+--+
                                 |          |
                      /api, /ws  |          |  Static Assets
                                 |          |
                        +--------v----+   +-v--------------+
                        | FastAPI App |   | React Frontend |
                        +---+------+--+   +----------------+
                            |      |
             AMQP (5672)    |      | SQL (5432)
       +--------------------+      +--------------------+
       |                                                |
+------v--------+                        +--------------v---------------+
| RabbitMQ      |                        | PostgreSQL (Multi-Database)  |
| - Exchanges   |                        | - bankflow_ai                |
| - Queues      |                        | - bankflow_ai_blr            |
| - DLQ         |                        | - bankflow_ai_che            |
+------+--------+                        | - bankflow_ai_hyd            |
       |                                 +--------------^---------------+
       | AMQP (5672)                                    | SQL (5432)
+------v------------------------------------------------+---------------+
| Mesa Simulation & Recovery Workers (Independent Scaling Replicas)     |
+-----------------------------------------------------------------------+
```

---

## 2. Docker Compose Deployment

### Prerequisites
- Docker Engine 24.0+
- Docker Compose v2.20+
- 4 CPU Cores, 8 GB RAM minimum recommended

### Step 1: Environment Configuration
Copy `.env.example` into `backend/.env`:
```bash
cp backend/.env.example backend/.env
```
Ensure strong secrets are defined for production:
- `JWT_SECRET_KEY`: Minimum 64-character random string.
- `DATA_ENCRYPTION_KEY`: 32-byte Base64-encoded key for AES-256-GCM.
- `BLR_BRANCH_SECRET`, `CHE_BRANCH_SECRET`, `HYD_BRANCH_SECRET`: Unique per-branch authentication keys.

### Step 2: Build & Start Containers
From the project root:
```bash
docker compose up -d --build
```

### Step 3: Verify Container Health
```bash
docker compose ps
```
All containers should report `healthy` or `running`:
- `bankflow-postgres` (Port 5432)
- `bankflow-rabbitmq` (Ports 5672, 15672)
- `bankflow-api` (Port 8000)
- `bankflow-worker` (Mesa agent background runner)
- `bankflow-frontend` (Port 80)

### Step 4: Run Branch Database Migrations & Seeding
```bash
docker compose exec api alembic upgrade head
docker compose exec api python -m app.federation.seed
```

---

## 3. Independent Service Deployment & Horizontal Scaling

Each component can be deployed and scaled independently in Kubernetes or cloud container platforms (AWS ECS, Google Cloud Run, Azure Container Apps):

### Scaling Agent Workers
The Mesa agent execution workers run independently of the HTTP API:
```bash
docker compose up -d --scale worker=3
```
Workers consume from RabbitMQ queues and synchronize request state in PostgreSQL with atomic versioning, preventing double-processing.

### High Availability PostgreSQL
In enterprise cloud environments, replace the single PostgreSQL container with managed Multi-AZ services:
- **AWS Aurora PostgreSQL** or **GCP Cloud SQL**.
- Point `DB_HOST` and branch-specific connection strings to the managed read/write endpoints.
- Ensure SSL connection mode is required (`sslmode=require`).

### RabbitMQ Enterprise Clustering
- Configure a 3-node RabbitMQ cluster with quorum queues for zero message loss.
- Enable dead-letter exchange (DLX) alerting for unprocessable messages.

---

## 4. Production Security & Hardening Checklist
1. **TLS / SSL Termination**:
   - Terminate HTTPS at Cloudflare, AWS ALB, or Nginx ingress using TLS 1.3.
   - Enforce HTTP Strict Transport Security (`HSTS`).
2. **Environment Variable Protection**:
   - Inject secrets using HashiCorp Vault, AWS Secrets Manager, or GCP Secret Manager.
   - Never commit `.env` or production secrets into source control.
3. **Database Network Isolation**:
   - Host PostgreSQL and RabbitMQ inside a private VPC subnet with no public IP.
   - Restrict inbound traffic strictly to the security group of the API and Worker containers.
4. **CORS Restrictions**:
   - Set `ALLOWED_ORIGINS` to the exact production domain (e.g. `https://bankflow.yourdomain.com`).
5. **Rate Limiting**:
   - Keep rate limiters enabled (`RATE_LIMIT_LOGIN_MAX_ATTEMPTS=5` per 5 minutes).

---

## 5. System Limitations & Operating Boundaries
- **Synthetic Banking Data Only**: BankFlow AI operates strictly on synthetic, simulated financial records. It contains no connectivity to real SWIFT, ACH, or central banking networks.
- **Simulation In-Memory Cache**: The Mesa agent space is an agent-based simulation model. PostgreSQL serves as the persistent, authoritative state of record.
- **Unity Replay**: Unity connects to FastAPI via WebSocket and REST APIs or reads exported JSON manifests for high-fidelity offline/online visual replay.
