# BankFlow AI – Simulation Engine

This directory is designated for the multi-agent banking workload simulation engine.

## Phase 1 Status
Per Phase 1 objectives, automated agent logic and workflow simulation scripts are not implemented yet. The database models (`Agent`, `Request`, `AuditLog`) and status lifecycle enums have been created to support future simulation requirements.

## Planned Simulation Capabilities (Future Phases)
- **Synthetic Traffic Generator**: Emulates synthetic customer request bursts across supported service types (Cheque Book, Debit Card Replacement, Address Update, Account Application).
- **Multi-Agent Orchestrator**: Simulates cooperative agent behaviors across Intake, Verification, Request, Service, and Supervisor agents.
- **Latency & Concurrency Simulator**: Evaluates concurrent routing throughput, conflict resolution, and exception escalations (needs correction, human review).

Simulation scripts will be developed in subsequent phases.
