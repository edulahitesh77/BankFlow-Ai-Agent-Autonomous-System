# BankFlow AI – Unity 2D Multi-Agent Visualization Dashboard Setup Guide

This guide details the complete setup, configuration, and demonstration procedures for the **Unity 2D Multi-Agent Visualization Dashboard** (Phase 9 of BankFlow AI).

---

## 1. System Requirements & Unity Version

- **Recommended Unity Versions**:
  - **Unity 2022.3 LTS** (e.g. 2022.3.15f1 or newer)
  - **Unity 6 (6000.0.x)**
- **Operating System**: Windows 10/11, macOS, or Linux.
- **Display Resolution**: Optimized for `1920 × 1080` (16:9 Full HD).
- **Backend Requirement (for Mode 2 Live Monitoring)**:
  - Python 3.12+ with FastAPI running on `http://127.0.0.1:8000`.
  - PostgreSQL database initialized with Alembic migrations.

---

## 2. Directory Structure

The complete Unity 2D project resides in `BankFlow-AI/unity-dashboard/`:

```
BankFlow-AI/unity-dashboard/
├── Packages/
│   └── manifest.json                    # 2D, uGUI, TextMeshPro, WebRequest dependencies
├── ProjectSettings/
│   ├── ProjectSettings.asset            # Display resolution & project metadata
│   ├── TagManager.asset                 # Tags, layers, and sorting layers
│   └── EditorBuildSettings.asset        # Active scenes configuration
└── Assets/
    ├── Scenes/
    │   └── BankFlowDashboard.unity       # Primary visual dashboard scene
    ├── Data/
    │   ├── sample_simulation.json       # Validated multi-tick benchmark replay dataset
    │   └── simulation_schema.json       # JSON Schema specification (v1.0.0)
    ├── Scripts/
    │   ├── Data/
    │   │   └── SimulationManifest.cs    # C# data models & schema validation
    │   ├── Managers/
    │   │   ├── SimulationManager.cs     # Master replay loop & mode manager
    │   │   ├── WorkflowManager.cs       # 8-Stage visual layout & token pool
    │   │   ├── AgentManager.cs          # Dynamic pool for N Request Agents
    │   │   ├── UIManager.cs             # Unified UI panel coordinator
    │   │   └── NetworkManager.cs        # FastAPI REST polling client
    │   ├── Agents/
    │   │   └── AgentController.cs       # Agent visual actors & health state colors
    │   ├── Requests/
    │   │   ├── RequestToken.cs          # Request cards with smooth Lerp motion
    │   │   └── WorkflowStageArea.cs     # Stage container & slot positioning
    │   ├── Visualization/
    │   │   ├── AgentLineRenderer.cs     # Dynamic communication links
    │   │   └── MessageTrajectory.cs     # Animated message packets & pulse effect
    │   ├── UI/
    │   │   ├── TopNavBar.cs             # Title, tick counters, mode toggle, speeds
    │   │   ├── AgentMonitorPanel.cs     # Real-time agent status counters
    │   │   ├── SupervisorPanel.cs       # Supervisor heartbeats & failover logs
    │   │   ├── MetricsPanel.cs          # Authoritative Python/Mesa KPI cards
    │   │   └── EventInspectionPanel.cs  # Drill-down request & agent event audit
    │   └── Replay/
    │       ├── ReplayController.cs      # Play/Pause/Step/Reset controller
    │       └── ReplayTimeline.cs        # Interactive timeline seek slider
    ├── Prefabs/
    │   ├── RequestTokenPrefab.prefab    # Visual card template for requests
    │   ├── AgentActorPrefab.prefab      # Visual actor template for agents
    │   └── MessagePacketPrefab.prefab   # Glowing message packet template
    └── Materials/
        ├── AgentHealthyMat.mat          # Emerald (#10B981)
        ├── AgentBusyMat.mat             # Cyan (#06B6D4)
        └── AgentFailedMat.mat           # Red (#EF4444)
```

---

## 3. Opening the Project in Unity

1. Open **Unity Hub**.
2. Click **Add** -> **Add project from disk**.
3. Select the folder:
   `c:\Users\edula\OneDrive\Documents\AI-SEM\BankFlow-AI\unity-dashboard`
4. Choose **Unity 2022.3 LTS** (or Unity 6) as the editor version.
5. Click to open the project. Unity will automatically resolve packages from `Packages/manifest.json`.
6. In the Unity Project window, navigate to `Assets/Scenes/` and double-click **`BankFlowDashboard.unity`**.
7. Press the **Play** button at the top of the Unity Editor to launch the dashboard.

---

## 4. Visualization Modes

The dashboard supports two operation modes via the top navigation bar toggle:

### Mode 1: Recorded Replay (Default)
- **Data Source**: Standalone JSON export files stored in `Assets/Data/sample_simulation.json`.
- **Functionality**:
  - Complete, client-side visual replay of deterministic multi-tick benchmark executions.
  - **Guaranteed Database Isolation**: Replaying, rewinding, or seeking does **never** mutate the PostgreSQL database.
  - **Schema Validation**: Rejects files missing required fields or having a `schema_version` other than `1.0.0`.
- **Interactive Controls**:
  - **Play / Pause**: Start or stop playback loop.
  - **Step Forward / Backward**: Advance or rewind by exactly 1 simulation tick.
  - **Timeline Slider**: Drag slider to jump immediately to any tick (Tick 0 to 14).
  - **Playback Speed**: Toggle between `0.5x`, `1.0x`, `2.0x`, and `5.0x`.
  - **Reset**: Return to Tick 0.

### Mode 2: Live Monitoring
- **Data Source**: Active FastAPI REST backend at `http://127.0.0.1:8000/api/bank/simulation/snapshot`.
- **Functionality**:
  - Queries live simulation ticks in real time via `NetworkManager`.
  - Displays actual PostgreSQL request states, dynamic agent allocations, and active queue counts.
  - Graceful connection handling: Shows `OFFLINE` if backend is stopped without crashing.

---

## 5. Visual Dashboard Architecture

### 1. 8-Stage Workflow Visualizer
The central canvas displays 8 distinct pipeline stages:
1. **Stage 1: Customer** (`NEW` requests submitted by customer agents)
2. **Stage 2: Intake** (`CLASSIFIED` requests categorized by Intake Agent)
3. **Stage 3: Assignment** (`QUEUED` requests dispatched to Request Agents)
4. **Stage 4: Verification** (`VERIFIED` requests validated for prerequisites)
5. **Stage 5: Service Execution** (`IN_SERVICE` requests executing core banking operations)
6. **Stage 6: Correction** (`NEEDS_CORRECTION` requests requiring customer adjustments)
7. **Stage 7: Human Review** (`HUMAN_REVIEW` requests escalated to bank officers)
8. **Stage 8: Finished** (`COMPLETED`, `REJECTED_INPUT`, or `FAILED` requests)

### 2. Request Cards
- **Color Coded by Banking Service**:
  - `CHEQUE_BOOK`: Indigo (`#6366F1`)
  - `DEBIT_CARD_REPLACEMENT`: Teal (`#14B8A6`)
  - `ADDRESS_UPDATE`: Blue (`#3B82F6`)
  - `ACCOUNT_APPLICATION`: Purple (`#8B5CF6`)
- **Metadata**: Request ID, priority badge (`HIGH`/`MEDIUM`), assigned agent, assignment version, retry count.
- **Interactivity**: Clicking any request token opens the **Event Inspection Panel** displaying its complete audit trail.

### 3. Dynamic Agent Monitoring Panel
- Supports **any arbitrary number ($N$) of Request Agents** (`RequestAgent_1` through `RequestAgent_N`).
- **Health State Mapping**:
  - `HEALTHY`: Green (`#10B981`)
  - `BUSY`: Cyan (`#06B6D4`)
  - `IDLE`: Slate (`#64748B`)
  - `UNRESPONSIVE`: Amber (`#F59E0B`)
  - `FAILED`: Red (`#EF4444`)
  - `RECOVERING`: Orange (`#F97316`)
- **Message Transmission Visualization**:
  - Glowing packets travel along message trajectories when agents communicate.
  - Receiving agents display an expanding radar pulse ring upon receiving tasks.

### 4. Supervisor & Fault Tolerance Panel
- **Heartbeat Status**: Displays supervisor liveliness checks.
- **Failure Recovery Telemetry**:
  - Detects agent unresponsiveness (e.g. `RequestAgent_2` heartbeat timeout at Tick 7).
  - Displays supervisor task reassignment to `RequestAgent_1` with incremented assignment version `2` and retry count `1` at Tick 8.
  - Circuit breaker operational status (`CLOSED`, `OPEN`, `HALF_OPEN`).

### 5. Authoritative Metrics & Analytics
- Calculated directly by Python/Mesa:
  - Total Requests, Completed, Failed, Pending, Human Review, Recovered.
  - Average Waiting Time (ticks), Average Completion Time (ticks).
  - System Throughput (req/min).
  - Request Agent Utilization Rate (%).
  - Message Integrity Rate (100.0%).

---

## 6. Demonstration & Viva Presentation Script

1. **Introduction**:
   - *"BankFlow AI demonstrates an educational multi-agent banking automation system. Python and Mesa serve as the authoritative simulation engine and source of truth, while Unity 2D provides an interactive visualization and replay dashboard."*
2. **Showcase Mode 1 (Recorded Replay)**:
   - Click **Play**: Observe request tokens smoothly moving across the 8 stages from Customer -> Intake -> Assignment -> Verification -> Service -> Completed.
   - Adjust **Speed** to `2.0x` and `5.0x` to show high-throughput playback.
   - Click **Pause**, then use **Step Forward** and the **Timeline Slider** to scrub to **Tick 07**.
3. **Demonstrate Failure Recovery (Ticks 07–09)**:
   - Point out `RequestAgent_2` turning **Amber (`UNRESPONSIVE`)** at Tick 7 on request `REQ-2026-SYN-0005`.
   - Step to **Tick 08**: Show `Supervisor Agent` detecting timeout and reassigning `REQ-2026-SYN-0005` to `RequestAgent_1` (assignment version 2, retry count 1).
   - Show the live event log in the **Supervisor Panel** recording `AGENT_TIMEOUT_DETECTED` and `TASK_REASSIGNED`.
4. **Demonstrate Event Drill-Down**:
   - Click on `REQ-2026-SYN-0005` or `RequestAgent_2` to open the **Event Inspection Panel** and display the full immutable event audit trail.
5. **Showcase Mode 2 (Live Monitoring)**:
   - Click **Mode Toggle** on the top navigation bar.
   - Show live synchronization with running FastAPI backend endpoints (`/api/bank/simulation/snapshot`).
