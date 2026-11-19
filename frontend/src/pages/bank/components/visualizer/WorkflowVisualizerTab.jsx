import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  ReactFlowProvider,
} from 'reactflow';
import 'reactflow/dist/style.css';

import {
  Activity,
  Play,
  Pause,
  RotateCw,
  Terminal,
  Workflow,
  BarChart2,
  Zap,
  ShieldCheck,
  Cpu,
  Layers,
  Search,
  Maximize2,
  Flame,
  Radio,
  Clock,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';

import { AgentNode } from './AgentNode';
import { SupervisorNode } from './SupervisorNode';
import { InfrastructureNode } from './InfrastructureNode';
import { AnimatedPacketEdge } from './AnimatedPacketEdge';
import { AgentInspectorDrawer } from './AgentInspectorDrawer';
import { EdgeInspectorDrawer } from './EdgeInspectorDrawer';
import { DecisionInspectorModal } from './DecisionInspectorModal';
import { RequestJourneyDrawer } from './RequestJourneyDrawer';
import { PerformanceAnalyticsDrawer } from './PerformanceAnalyticsDrawer';
import { LiveEventTimeline } from './LiveEventTimeline';

import {
  getStoredToken,
  fetchRealtimeAgentMonitoring,
  startSimulation,
  stopSimulation,
  runSimulationScenario,
  fetchVisualizerReplayManifest,
} from '../../../../api/auth';

const nodeTypes = {
  agentNode: AgentNode,
  supervisorNode: SupervisorNode,
  infrastructureNode: InfrastructureNode,
};

const edgeTypes = {
  animatedPacket: AnimatedPacketEdge,
};

export const WorkflowVisualizerTab = () => {
  // Live Telemetry state
  const [monitoringData, setMonitoringData] = useState(null);
  const [connectionType, setConnectionType] = useState('CONNECTING'); // 'WEBSOCKET' | 'POLLING'
  const [isLiveRunning, setIsLiveRunning] = useState(false);
  const [lastEvent, setLastEvent] = useState(null);

  // Mode: 'LIVE' | 'REPLAY'
  const [mode, setMode] = useState('LIVE');

  // Replay Controller state
  const [replayManifest, setReplayManifest] = useState(null);
  const [replayTick, setReplayTick] = useState(0);
  const [isPlayingReplay, setIsPlayingReplay] = useState(false);
  const [replaySpeed, setReplaySpeed] = useState(1); // 0.5, 1, 2, 5
  const replayTimerRef = useRef(null);

  // Inspector Drawers state
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [selectedEdge, setSelectedEdge] = useState(null);
  const [decisionModalOpen, setDecisionModalOpen] = useState(false);
  const [journeyDrawerOpen, setJourneyDrawerOpen] = useState(false);
  const [journeyRequestId, setJourneyRequestId] = useState(null);
  const [analyticsDrawerOpen, setAnalyticsDrawerOpen] = useState(false);

  // Timeline pause state (pauses visual stream without pausing backend)
  const [isStreamPaused, setIsStreamPaused] = useState(false);
  const frozenEventsRef = useRef([]);

  // React Flow Nodes & Edges State
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Action / Benchmark execution state
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);
  const [benchmarkMsg, setBenchmarkMsg] = useState(null);

  const wsRef = useRef(null);
  const pollTimerRef = useRef(null);
  const reactFlowInstanceRef = useRef(null);

  // ==========================================================================
  // 1. DATA FETCHING & WEBSOCKET ENGINE
  // ==========================================================================

  const fetchLiveSnapshot = useCallback(async () => {
    try {
      const data = await fetchRealtimeAgentMonitoring();
      if (!isStreamPaused) {
        setMonitoringData(data);
        setIsLiveRunning(data.is_running);
        if (data.events && data.events.length > 0) {
          setLastEvent(data.events[0]);
        }
      }
    } catch (err) {
      console.error('Failed to fetch visualizer snapshot:', err);
    }
  }, [isStreamPaused]);

  useEffect(() => {
    let isMounted = true;
    const token = getStoredToken();

    const startPolling = () => {
      if (!isMounted) return;
      setConnectionType('POLLING');
      fetchLiveSnapshot();
      if (!pollTimerRef.current) {
        pollTimerRef.current = setInterval(fetchLiveSnapshot, 2000);
      }
    };

    const stopPolling = () => {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    };

    const connectWebSocket = () => {
      if (!token) {
        startPolling();
        return;
      }

      try {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.port === '5173' ? `${window.location.hostname}:8000` : window.location.host;
        const wsUrl = `${wsProtocol}//${host}/ws/agents/monitoring?token=${encodeURIComponent(token)}`;

        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          if (!isMounted) return;
          setConnectionType('WEBSOCKET');
          stopPolling();
        };

        ws.onmessage = (event) => {
          if (!isMounted || mode !== 'LIVE' || isStreamPaused) return;
          try {
            const parsed = JSON.parse(event.data);
            setMonitoringData(parsed);
            setIsLiveRunning(parsed.is_running);
            if (parsed.events && parsed.events.length > 0) {
              setLastEvent(parsed.events[0]);
            }
          } catch (e) {
            console.error('WebSocket JSON parse error in visualizer:', e);
          }
        };

        ws.onerror = () => startPolling();
        ws.onclose = () => startPolling();
      } catch (err) {
        startPolling();
      }
    };

    fetchLiveSnapshot().then(() => {
      connectWebSocket();
    });

    return () => {
      isMounted = false;
      stopPolling();
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [fetchLiveSnapshot, mode, isStreamPaused]);

  // ==========================================================================
  // 2. REPLAY ENGINE (REPLAY MODE)
  // ==========================================================================

  const loadReplayData = async () => {
    try {
      const manifest = await fetchVisualizerReplayManifest();
      setReplayManifest(manifest);
      setReplayTick(0);
      setIsPlayingReplay(false);
    } catch (err) {
      console.error('Failed to load replay manifest:', err);
    }
  };

  useEffect(() => {
    if (mode === 'REPLAY' && !replayManifest) {
      loadReplayData();
    }
  }, [mode, replayManifest]);

  useEffect(() => {
    if (mode !== 'REPLAY' || !isPlayingReplay || !replayManifest) return;

    const intervalTime = Math.max(200, 1000 / replaySpeed);
    replayTimerRef.current = setInterval(() => {
      setReplayTick((prev) => {
        const total = (replayManifest.snapshots || []).length;
        if (prev + 1 >= total) {
          setIsPlayingReplay(false);
          return prev;
        }
        return prev + 1;
      });
    }, intervalTime);

    return () => {
      if (replayTimerRef.current) clearInterval(replayTimerRef.current);
    };
  }, [mode, isPlayingReplay, replayManifest, replaySpeed]);

  // ==========================================================================
  // 3. TOPOLOGY & DYNAMIC AGENT GRAPH BUILDER
  // ==========================================================================

  useEffect(() => {
    let sourceAgents = [];
    let activeEvent = lastEvent;

    if (mode === 'LIVE') {
      sourceAgents = monitoringData?.agents || [];
    } else if (mode === 'REPLAY' && replayManifest?.snapshots) {
      const currentSnapshot = replayManifest.snapshots[replayTick] || {};
      const activeReqs = currentSnapshot.active_requests || [];
      // Reconstruct simulated agents from snapshot
      sourceAgents = [
        {
          id: 1,
          agent_code: 'AGT-CUST-SIM-01',
          agent_name: 'Customer Agent',
          agent_type: 'CUSTOMER',
          status: 'BUSY',
          current_request_id: activeReqs[0]?.request_id || null,
          completed_tasks: replayTick * 2,
        },
        {
          id: 2,
          agent_code: 'AGT-INTAKE-01',
          agent_name: 'Intake Agent',
          agent_type: 'INTAKE',
          status: 'PROCESSING',
          current_request_id: activeReqs[1]?.request_id || null,
          completed_tasks: replayTick * 2,
        },
        {
          id: 3,
          agent_code: 'RequestAgent_0',
          agent_name: 'Request Worker 0',
          agent_type: 'REQUEST',
          status: 'PROCESSING',
          current_request_id: activeReqs[2]?.request_id || null,
          completed_tasks: replayTick,
        },
        {
          id: 4,
          agent_code: 'RequestAgent_1',
          agent_name: 'Request Worker 1',
          agent_type: 'REQUEST',
          status: 'IDLE',
          current_request_id: null,
          completed_tasks: replayTick,
        },
        {
          id: 5,
          agent_code: 'AGT-VERIF-01',
          agent_name: 'Verification Agent',
          agent_type: 'VERIFICATION',
          status: 'VERIFYING',
          current_request_id: activeReqs[3]?.request_id || null,
          completed_tasks: replayTick,
        },
        {
          id: 6,
          agent_code: 'ServiceAgent_CHEQUE_BOOK',
          agent_name: 'Service Worker',
          agent_type: 'SERVICE',
          status: 'PROCESSING',
          current_request_id: activeReqs[4]?.request_id || null,
          completed_tasks: replayTick,
        },
        {
          id: 7,
          agent_code: 'AGT-SUPERVISOR-01',
          agent_name: 'Supervisor Agent',
          agent_type: 'SUPERVISOR',
          status: 'IDLE',
          completed_tasks: 0,
        },
      ];
      if (replayManifest.events && replayManifest.events[replayTick]) {
        activeEvent = replayManifest.events[replayTick];
      }
    }

    // Separate agents by role
    const customerAgent = sourceAgents.find((a) => a.agent_type === 'CUSTOMER') || {
      agent_code: 'AGT-CUST-SIM-01',
      agent_name: 'Customer Agent',
      agent_type: 'CUSTOMER',
      status: 'IDLE',
    };

    const intakeAgent = sourceAgents.find((a) => a.agent_type === 'INTAKE') || {
      agent_code: 'AGT-INTAKE-01',
      agent_name: 'Intake & Classification Agent',
      agent_type: 'INTAKE',
      status: 'IDLE',
    };

    const verificationAgent = sourceAgents.find((a) => a.agent_type === 'VERIFICATION') || {
      agent_code: 'AGT-VERIF-01',
      agent_name: 'Verification Agent',
      agent_type: 'VERIFICATION',
      status: 'IDLE',
    };

    const supervisorAgent = sourceAgents.find((a) => a.agent_type === 'SUPERVISOR') || {
      agent_code: 'AGT-SUPERVISOR-01',
      agent_name: 'Supervisor Agent',
      agent_type: 'SUPERVISOR',
      status: 'IDLE',
    };

    // Dynamic Request Agents pool
    const requestAgents = sourceAgents.filter((a) => a.agent_type === 'REQUEST');
    const displayRequestAgents =
      requestAgents.length > 0
        ? requestAgents
        : [
            { agent_code: 'RequestAgent_0', agent_name: 'Request Worker 0', agent_type: 'REQUEST', status: 'IDLE' },
            { agent_code: 'RequestAgent_1', agent_name: 'Request Worker 1', agent_type: 'REQUEST', status: 'IDLE' },
            { agent_code: 'RequestAgent_2', agent_name: 'Request Worker 2', agent_type: 'REQUEST', status: 'IDLE' },
          ];

    // Service agents pool
    const serviceAgents = sourceAgents.filter((a) => a.agent_type === 'SERVICE');
    const serviceLead = serviceAgents[0] || {
      agent_code: 'ServiceAgent_POOL',
      agent_name: 'Service Worker Pool',
      agent_type: 'SERVICE',
      status: 'IDLE',
      completed_tasks: 0,
    };

    // Calculate layout coordinates
    const calculatedNodes = [
      // 1. Supervisor Agent (Top Anchor overseeing the fleet)
      {
        id: 'supervisor-node',
        type: 'supervisorNode',
        position: { x: 740, y: 30 },
        data: {
          ...supervisorAgent,
          monitored_count: sourceAgents.length,
          unresponsive_count: sourceAgents.filter((a) => a.status === 'FAILED' || a.status === 'UNRESPONSIVE').length,
          recovery_count: monitoringData?.metrics?.failed_requests || 0,
        },
      },

      // 2. Customer Agent (Left entry point)
      {
        id: 'customer-node',
        type: 'agentNode',
        position: { x: 40, y: 300 },
        data: customerAgent,
      },

      // 3. Intake Agent (Classification & validation)
      {
        id: 'intake-node',
        type: 'agentNode',
        position: { x: 340, y: 300 },
        data: intakeAgent,
      },

      // 4. RabbitMQ Message Broker
      {
        id: 'rabbitmq-node',
        type: 'infrastructureNode',
        position: { x: 640, y: 300 },
        data: {
          type: 'RABBITMQ',
          title: 'RabbitMQ Message Broker',
          subtitle: 'amqp://127.0.0.1:5672',
          metric_label: 'Topics / Queues',
          metric_value: '6 Active Queues',
          status: 'CONNECTED',
        },
      },

      // 5. Dynamic Request Agents Pool (Laid out in neat vertical column)
      ...displayRequestAgents.map((rag, idx) => {
        // Vertical spacing offset based on count
        const startY = 160;
        const spacingY = 130;
        return {
          id: `req-agent-node-${idx}`,
          type: 'agentNode',
          position: { x: 940, y: startY + idx * spacingY },
          data: rag,
        };
      }),

      // 6. Verification Agent
      {
        id: 'verif-node',
        type: 'agentNode',
        position: { x: 1250, y: 300 },
        data: verificationAgent,
      },

      // 7. Service Agent Pool
      {
        id: 'service-node',
        type: 'agentNode',
        position: { x: 1550, y: 300 },
        data: serviceLead,
      },

      // 8. PostgreSQL Primary Database
      {
        id: 'postgres-node',
        type: 'infrastructureNode',
        position: { x: 1850, y: 300 },
        data: {
          type: 'POSTGRESQL',
          title: 'PostgreSQL Registry',
          subtitle: 'Authoritative State Registry',
          metric_label: 'Total Requests',
          metric_value: `${monitoringData?.metrics?.total_requests || 0} Records`,
          status: 'AUTHORITATIVE',
        },
      },
    ];

    // Determine which edge is currently active based on real event stream
    const evType = activeEvent?.event_type || '';
    const evReqId = activeEvent?.request_id || '';
    const evAgent = activeEvent?.agent_id || '';

    const isCustomerToIntake =
      evType === 'REQUEST_CREATED' || evType === 'CUSTOMER_CORRECTION_SUBMITTED';
    const isIntakeToRabbit =
      evType === 'REQUEST_CLASSIFIED' || evType === 'INTAKE_ACCEPTED';
    const isRabbitToReq =
      evType === 'REQUEST_ASSIGNED' || evType === 'REQUEST_ACCEPTED' || evType === 'REQUEST_DISPATCHED';
    const isReqToVerif =
      evType === 'VERIFICATION_STARTED' || evType === 'VERIFICATION_COMPLETED';
    const isVerifToService =
      evType === 'SERVICE_STARTED' || evType === 'SERVICE_COMPLETED';
    const isServiceToDb =
      evType === 'REQUEST_COMPLETED' || evType === 'RECORD_SAVED';
    const isSupervisorActive =
      evType === 'AGENT_FAILED' || evType === 'RECOVERY_COMPLETED' || evType === 'HEARTBEAT_TIMEOUT';

    // Build directed edges with animated packet indicators
    const calculatedEdges = [
      // Customer -> Intake
      {
        id: 'edge-cust-intake',
        source: 'customer-node',
        target: 'intake-node',
        type: 'animatedPacket',
        data: {
          label: 'customer.intake',
          routing_key: 'request.created',
          active_event: isCustomerToIntake ? evType : null,
          request_id: isCustomerToIntake ? evReqId : null,
          is_active: isCustomerToIntake,
        },
      },

      // Intake -> RabbitMQ
      {
        id: 'edge-intake-rabbit',
        source: 'intake-node',
        target: 'rabbitmq-node',
        type: 'animatedPacket',
        data: {
          label: 'exchange.classified',
          routing_key: 'bankflow.direct.intake',
          active_event: isIntakeToRabbit ? evType : null,
          request_id: isIntakeToRabbit ? evReqId : null,
          is_active: isIntakeToRabbit,
        },
      },

      // RabbitMQ -> Dynamic Request Agents
      ...displayRequestAgents.map((rag, idx) => {
        const isThisReqActive = isRabbitToReq && (evAgent === rag.agent_code || idx === 0);
        return {
          id: `edge-rabbit-req-${idx}`,
          source: 'rabbitmq-node',
          target: `req-agent-node-${idx}`,
          type: 'animatedPacket',
          data: {
            label: `pool.worker.${idx}`,
            routing_key: `bankflow.queue.${rag.agent_code}`,
            active_event: isThisReqActive ? evType : null,
            request_id: isThisReqActive ? evReqId : null,
            is_active: isThisReqActive,
          },
        };
      }),

      // Dynamic Request Agents -> Verification
      ...displayRequestAgents.map((rag, idx) => {
        const isThisVerifActive = isReqToVerif && (evAgent === rag.agent_code || idx === 0);
        return {
          id: `edge-req-verif-${idx}`,
          source: `req-agent-node-${idx}`,
          target: 'verif-node',
          type: 'animatedPacket',
          data: {
            label: 'request.verify',
            routing_key: 'bankflow.direct.verification',
            active_event: isThisVerifActive ? evType : null,
            request_id: isThisVerifActive ? evReqId : null,
            is_active: isThisVerifActive,
          },
        };
      }),

      // Verification -> Service
      {
        id: 'edge-verif-service',
        source: 'verif-node',
        target: 'service-node',
        type: 'animatedPacket',
        data: {
          label: 'service.execute',
          routing_key: 'bankflow.direct.service',
          active_event: isVerifToService ? evType : null,
          request_id: isVerifToService ? evReqId : null,
          is_active: isVerifToService,
        },
      },

      // Service -> PostgreSQL
      {
        id: 'edge-service-postgres',
        source: 'service-node',
        target: 'postgres-node',
        type: 'animatedPacket',
        data: {
          label: 'sql.commit',
          routing_key: 'authoritative.settlement',
          active_event: isServiceToDb ? evType : null,
          request_id: isServiceToDb ? evReqId : null,
          is_active: isServiceToDb,
        },
      },

      // Supervisor -> Nodes (Supervisory Heartbeat lines)
      {
        id: 'edge-supervisor-intake',
        source: 'supervisor-node',
        sourceHandle: 'supervisor-out',
        target: 'intake-node',
        targetHandle: 'top',
        type: 'animatedPacket',
        data: {
          is_supervisor_link: true,
          label: 'heartbeat.ping',
          is_active: isSupervisorActive,
          active_event: isSupervisorActive ? 'SUPERVISION_HEAL' : null,
        },
      },
      {
        id: 'edge-supervisor-rabbit',
        source: 'supervisor-node',
        sourceHandle: 'supervisor-out',
        target: 'rabbitmq-node',
        targetHandle: 'top',
        type: 'animatedPacket',
        data: {
          is_supervisor_link: true,
          label: 'broker.health',
          is_active: isSupervisorActive,
        },
      },
      {
        id: 'edge-supervisor-verif',
        source: 'supervisor-node',
        sourceHandle: 'supervisor-out',
        target: 'verif-node',
        targetHandle: 'top',
        type: 'animatedPacket',
        data: {
          is_supervisor_link: true,
          label: 'compliance.audit',
          is_active: isSupervisorActive,
        },
      },
    ];

    setNodes(calculatedNodes);
    setEdges(calculatedEdges);
  }, [monitoringData, mode, replayManifest, replayTick, lastEvent, setNodes, setEdges]);

  // Node & Edge selection handlers
  const handleNodeClick = useCallback((event, node) => {
    setSelectedEdge(null);
    setSelectedAgent(node.data);
  }, []);

  const handleEdgeClick = useCallback((event, edge) => {
    setSelectedAgent(null);
    setSelectedEdge(edge);
  }, []);

  const handlePaneClick = useCallback(() => {
    setSelectedAgent(null);
    setSelectedEdge(null);
  }, []);

  // Trigger test benchmark
  const handleRunBenchmark = async () => {
    setBenchmarkLoading(true);
    setBenchmarkMsg(null);
    try {
      await runSimulationScenario(1);
      setBenchmarkMsg('Concurrent benchmark requests injected! Watch agents process simultaneously.');
      await fetchLiveSnapshot();
    } catch (err) {
      setBenchmarkMsg(`Benchmark error: ${err.message}`);
    } finally {
      setBenchmarkLoading(false);
    }
  };

  // Toggle Stream Pause
  const handleToggleStreamPause = () => {
    setIsStreamPaused((prev) => !prev);
  };

  // Open Request Journey Drawer
  const handleOpenJourney = (reqId) => {
    setJourneyRequestId(reqId);
    setJourneyDrawerOpen(true);
  };

  // Fit view helper
  const handleFitView = () => {
    if (reactFlowInstanceRef.current) {
      reactFlowInstanceRef.current.fitView({ padding: 0.15, duration: 600 });
    }
  };

  const metrics = monitoringData?.metrics || {
    total_requests: 0,
    processed_requests: 0,
    failed_requests: 0,
    pending_requests: 0,
    active_workers: 0,
  };

  return (
    <div className="space-y-6">
      {/* Top Action Bar & Mode Switcher */}
      <div className="bg-[#091124] border border-slate-800 rounded-2xl p-4 sm:p-5 shadow-xl flex flex-wrap items-center justify-between gap-4">
        {/* Title & Live Status */}
        <div className="flex items-center space-x-3.5">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-emerald-500/20 via-cyan-500/20 to-indigo-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shadow-lg">
            <Workflow className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2.5">
              <h2 className="text-lg font-bold text-white tracking-tight">AI Workflow Visualizer</h2>
              {mode === 'LIVE' ? (
                isLiveRunning ? (
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center space-x-1.5 shadow-sm">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                    <span>LIVE STREAM</span>
                  </span>
                ) : (
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-red-500/20 text-red-300 border border-red-500/40 font-mono">
                    SIMULATION STOPPED
                  </span>
                )
              ) : (
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/40 font-mono flex items-center space-x-1">
                  <span>📼 REPLAY MODE</span>
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Interactive node graph displaying real-time agent message routing, decisions, and telemetry
            </p>
          </div>
        </div>

        {/* Mode Toggle & Feature Toolbar */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Mode Switch (LIVE vs REPLAY) */}
          <div className="flex items-center rounded-xl bg-slate-950 p-1 border border-slate-800">
            <button
              onClick={() => {
                setMode('LIVE');
                setIsPlayingReplay(false);
              }}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                mode === 'LIVE'
                  ? 'bg-emerald-500 text-slate-950 shadow-md font-bold'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Live Telemetry
            </button>
            <button
              onClick={() => {
                setMode('REPLAY');
              }}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                mode === 'REPLAY'
                  ? 'bg-purple-500 text-white shadow-md font-bold'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Recorded Replay
            </button>
          </div>

          {/* Decision Inspector Trigger */}
          <button
            onClick={() => setDecisionModalOpen(true)}
            className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 transition shadow-sm"
          >
            <Terminal className="w-3.5 h-3.5 text-indigo-400" />
            <span>Decisions</span>
          </button>

          {/* Request Journey Trigger */}
          <button
            onClick={() => setJourneyDrawerOpen(true)}
            className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 transition shadow-sm"
          >
            <Workflow className="w-3.5 h-3.5 text-cyan-400" />
            <span>Journey Inspector</span>
          </button>

          {/* Fleet Analytics Trigger */}
          <button
            onClick={() => setAnalyticsDrawerOpen(true)}
            className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 border border-purple-500/30 transition shadow-sm"
          >
            <BarChart2 className="w-3.5 h-3.5 text-purple-400" />
            <span>Analytics</span>
          </button>

          {/* Concurrent Benchmark Runner */}
          <button
            onClick={handleRunBenchmark}
            disabled={benchmarkLoading}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-bold text-slate-950 bg-gradient-to-r from-emerald-400 to-cyan-400 hover:from-emerald-300 hover:to-cyan-300 transition shadow-lg shadow-emerald-500/10 disabled:opacity-50"
          >
            <Flame className="w-3.5 h-3.5" />
            <span>{benchmarkLoading ? 'Dispatching...' : 'Test Swarm'}</span>
          </button>
        </div>
      </div>

      {benchmarkMsg && (
        <div className="p-3 rounded-xl bg-cyan-950/60 border border-cyan-800 text-xs text-cyan-200 flex items-center justify-between">
          <span>{benchmarkMsg}</span>
          <button onClick={() => setBenchmarkMsg(null)} className="text-cyan-400 font-bold hover:text-white">
            Dismiss
          </button>
        </div>
      )}

      {/* Replay Controller Bar (Visible only in REPLAY mode) */}
      {mode === 'REPLAY' && (
        <div className="bg-[#0b1429] border border-purple-500/30 rounded-2xl p-4 shadow-xl flex flex-wrap items-center justify-between gap-4 animate-fadeIn">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setIsPlayingReplay((prev) => !prev)}
              className="w-9 h-9 rounded-xl bg-purple-500 hover:bg-purple-400 text-white flex items-center justify-center shadow-lg transition"
            >
              {isPlayingReplay ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current ml-0.5" />}
            </button>

            <button
              onClick={() => {
                const total = (replayManifest?.snapshots || []).length;
                setReplayTick((prev) => Math.min(total - 1, prev + 1));
              }}
              className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
            >
              Step +1
            </button>

            <button
              onClick={() => {
                setReplayTick(0);
                setIsPlayingReplay(false);
              }}
              className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
            >
              Reset
            </button>
          </div>

          {/* Timeline Scrubber */}
          <div className="flex-1 min-w-[200px] max-w-md flex items-center space-x-3">
            <span className="text-xs font-mono text-slate-400">Tick:</span>
            <input
              type="range"
              min={0}
              max={Math.max(0, (replayManifest?.snapshots || []).length - 1)}
              value={replayTick}
              onChange={(e) => {
                setReplayTick(Number(e.target.value));
                setIsPlayingReplay(false);
              }}
              className="flex-1 accent-purple-500 cursor-pointer"
            />
            <span className="font-mono text-xs font-bold text-purple-300">
              {replayTick} / {Math.max(0, (replayManifest?.snapshots || []).length - 1)}
            </span>
          </div>

          {/* Speed Multipliers */}
          <div className="flex items-center space-x-1.5 text-xs">
            <span className="text-slate-400 font-mono mr-1">Speed:</span>
            {[0.5, 1, 2, 5].map((spd) => (
              <button
                key={spd}
                onClick={() => setReplaySpeed(spd)}
                className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold transition ${
                  replaySpeed === spd
                    ? 'bg-purple-500 text-white'
                    : 'bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                {spd}x
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Interactive React Flow Canvas */}
      <div className="relative w-full h-[650px] bg-[#070d1e] border border-slate-800 rounded-3xl overflow-hidden shadow-2xl">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={handleNodeClick}
          onEdgeClick={handleEdgeClick}
          onPaneClick={handlePaneClick}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          fitViewOptions={{ padding: 0.12 }}
          minZoom={0.2}
          maxZoom={2.0}
          onInit={(instance) => {
            reactFlowInstanceRef.current = instance;
          }}
          className="bg-[#070d1e]"
        >
          <Background color="#1e293b" gap={24} size={1.2} />
          <Controls className="!bg-[#091124] !border-slate-800 !rounded-xl overflow-hidden shadow-xl fill-slate-300" />
          <MiniMap
            nodeStrokeColor="#10b981"
            nodeColor="#091124"
            maskColor="rgba(7, 13, 30, 0.75)"
            className="!bg-[#091124] !border-slate-800 !rounded-xl overflow-hidden shadow-xl"
          />
        </ReactFlow>

        {/* Floating Canvas Quick Controls (Top-Right) */}
        <div className="absolute top-4 right-4 z-10 flex items-center space-x-2">
          <button
            onClick={handleFitView}
            className="p-2 rounded-xl bg-slate-900/90 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700 shadow-lg backdrop-blur-md transition"
            title="Fit to Screen"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>

        {/* Floating Metrics Pill (Bottom-Left) */}
        <div className="absolute bottom-4 left-4 z-10 hidden sm:flex items-center space-x-3 px-4 py-2 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl backdrop-blur-md text-xs font-mono">
          <div className="flex items-center space-x-1.5 text-slate-400">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
            <span>Active Workers:</span>
            <span className="text-white font-bold">{metrics.active_workers}</span>
          </div>
          <span className="text-slate-700">•</span>
          <div className="flex items-center space-x-1 text-slate-400">
            <span>Processed:</span>
            <span className="text-emerald-400 font-bold">{metrics.processed_requests}</span>
          </div>
          <span className="text-slate-700">•</span>
          <div className="flex items-center space-x-1 text-slate-400">
            <span>In-Flight:</span>
            <span className="text-indigo-400 font-bold">{metrics.pending_requests}</span>
          </div>
        </div>
      </div>

      {/* Live Event Timeline Stream */}
      <LiveEventTimeline
        events={monitoringData?.events || []}
        isStreamPaused={isStreamPaused}
        onTogglePause={handleToggleStreamPause}
        onSelectRequest={handleOpenJourney}
      />

      {/* Modals & Slide-out Drawers */}
      <AgentInspectorDrawer
        agent={selectedAgent}
        onClose={() => setSelectedAgent(null)}
        onSelectRequest={handleOpenJourney}
      />

      <EdgeInspectorDrawer
        edge={selectedEdge}
        onClose={() => setSelectedEdge(null)}
        onSelectRequest={handleOpenJourney}
      />

      <DecisionInspectorModal
        isOpen={decisionModalOpen}
        onClose={() => setDecisionModalOpen(false)}
        onSelectRequest={handleOpenJourney}
      />

      <RequestJourneyDrawer
        isOpen={journeyDrawerOpen}
        initialRequestId={journeyRequestId}
        onClose={() => setJourneyDrawerOpen(false)}
        onSelectRequest={handleOpenJourney}
      />

      <PerformanceAnalyticsDrawer
        isOpen={analyticsDrawerOpen}
        onClose={() => setAnalyticsDrawerOpen(false)}
      />
    </div>
  );
};
