import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Cpu,
  Layers,
  Activity,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Play,
  Square,
  RotateCw,
  Terminal,
  Zap,
  BarChart2,
  Clock,
  Users,
  Loader2,
  Radio,
  ArrowRight,
  Filter,
  AlertTriangle,
  RefreshCw,
  ShieldAlert,
  Server,
  Workflow,
  CheckCircle,
  XCircle,
  Hash,
} from 'lucide-react';
import {
  getStoredToken,
  fetchRealtimeAgentMonitoring,
  startSimulation,
  stopSimulation,
  runSimulationScenario,
} from '../../../api/auth';

export const AgentMonitoringTab = () => {
  // Real-time telemetry state from backend
  const [monitoringData, setMonitoringData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [connectionType, setConnectionType] = useState('CONNECTING'); // 'WEBSOCKET' | 'POLLING' | 'CONNECTING'
  const [lastUpdated, setLastUpdated] = useState(null);

  // Engine control state
  const [actionLoading, setActionLoading] = useState(false);
  const [scenarioLoading, setScenarioLoading] = useState(false);
  const [selectedScenario, setSelectedScenario] = useState(1);
  const [scenarioResult, setScenarioResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Filters
  const [agentCategoryFilter, setAgentCategoryFilter] = useState('ALL'); // ALL, CORE, REQUEST, SERVICE, SUPERVISOR
  const [eventCategoryFilter, setEventCategoryFilter] = useState('ALL'); // ALL, COMMUNICATION, ASSIGNMENT, COMPLETION, FAILURE, RECOVERY

  const wsRef = useRef(null);
  const pollTimerRef = useRef(null);

  // Fallback REST Polling Handler
  const fetchSnapshot = useCallback(async () => {
    try {
      const data = await fetchRealtimeAgentMonitoring();
      setMonitoringData(data);
      setLastUpdated(new Date());
      setErrorMsg(null);
    } catch (err) {
      console.error('Error fetching real-time agent telemetry:', err);
      setErrorMsg(err.message || 'Failed to retrieve agent monitoring telemetry.');
    } finally {
      setLoading(false);
    }
  }, []);

  // WebSocket Connection Management with Auto-Fallback
  useEffect(() => {
    let isMounted = true;
    const token = getStoredToken();

    const startPolling = () => {
      if (!isMounted) return;
      setConnectionType('POLLING');
      fetchSnapshot();
      if (!pollTimerRef.current) {
        pollTimerRef.current = setInterval(fetchSnapshot, 2000);
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
        // Connect via Vite proxy or direct port 8000
        const host = window.location.port === '5173' ? `${window.location.hostname}:8000` : window.location.host;
        const wsUrl = `${wsProtocol}//${host}/ws/agents/monitoring?token=${encodeURIComponent(token)}`;

        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          if (!isMounted) return;
          setConnectionType('WEBSOCKET');
          setLoading(false);
          stopPolling();
        };

        ws.onmessage = (event) => {
          if (!isMounted) return;
          try {
            const parsed = JSON.parse(event.data);
            setMonitoringData(parsed);
            setLastUpdated(new Date());
            setErrorMsg(null);
          } catch (e) {
            console.error('WebSocket JSON parse error:', e);
          }
        };

        ws.onerror = () => {
          // Fallback to polling seamlessly
          startPolling();
        };

        ws.onclose = () => {
          startPolling();
        };
      } catch (err) {
        startPolling();
      }
    };

    // Initial fetch to load immediately
    fetchSnapshot().then(() => {
      connectWebSocket();
    });

    return () => {
      isMounted = false;
      stopPolling();
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [fetchSnapshot]);

  // Simulation Controls
  const handleStartSimulation = async () => {
    setActionLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      await startSimulation({
        num_request_agents: 4,
        tick_delay_seconds: 0.5,
        scenario_name: 'LIVE_AGENT_MONITORING',
      });
      setSuccessMsg('Simulation engine started successfully. Multi-agent swarm active.');
      await fetchSnapshot();
    } catch (err) {
      setErrorMsg(err.message || 'Failed to start simulation.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleStopSimulation = async () => {
    setActionLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      await stopSimulation();
      setSuccessMsg('Simulation engine stopped successfully.');
      await fetchSnapshot();
    } catch (err) {
      setErrorMsg(err.message || 'Failed to stop simulation.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRunScenario = async () => {
    setScenarioLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    setScenarioResult(null);
    try {
      const result = await runSimulationScenario(selectedScenario);
      setScenarioResult(result);
      setSuccessMsg(`Scenario ${selectedScenario} benchmark completed successfully.`);
      await fetchSnapshot();
    } catch (err) {
      setErrorMsg(err.message || 'Failed to execute benchmark scenario.');
    } finally {
      setScenarioLoading(false);
    }
  };

  const isRunning = monitoringData?.is_running ?? false;
  const metrics = monitoringData?.metrics || {
    total_requests: 0,
    processed_requests: 0,
    failed_requests: 0,
    pending_requests: 0,
    human_review_requests: 0,
    correction_requests: 0,
    active_workers: 0,
    total_agents: 0,
    idle_agents: 0,
  };

  const allAgents = monitoringData?.agents || [];
  const events = monitoringData?.events || [];

  // Categorize agents
  const coreAgents = allAgents.filter((a) => a.category === 'CORE_PIPELINE' || a.category === 'SUPERVISOR');
  const requestAgents = allAgents.filter((a) => a.category === 'REQUEST_POOL');
  const serviceAgents = allAgents.filter((a) => a.category === 'SERVICE_POOL');

  // Filter agents for table
  const displayedAgents = allAgents.filter((a) => {
    if (agentCategoryFilter === 'CORE') return a.category === 'CORE_PIPELINE' || a.category === 'SUPERVISOR';
    if (agentCategoryFilter === 'REQUEST') return a.category === 'REQUEST_POOL';
    if (agentCategoryFilter === 'SERVICE') return a.category === 'SERVICE_POOL';
    return true;
  });

  // Filter events
  const displayedEvents = events.filter((ev) => {
    if (eventCategoryFilter === 'ALL') return true;
    return ev.category === eventCategoryFilter;
  });

  const getStatusBadge = (status) => {
    switch (status) {
      case 'PROCESSING':
        return 'bg-cyan-950/80 text-cyan-400 border border-cyan-700/60 ring-1 ring-cyan-500/30';
      case 'BUSY':
        return 'bg-amber-950/80 text-amber-400 border border-amber-700/60 ring-1 ring-amber-500/30';
      case 'IDLE':
        return 'bg-slate-900/90 text-slate-300 border border-slate-700';
      case 'FAILED':
        return 'bg-red-950/80 text-red-400 border border-red-700/60 ring-1 ring-red-500/30';
      case 'RECOVERING':
        return 'bg-orange-950/80 text-orange-400 border border-orange-700/60 animate-pulse';
      default:
        return 'bg-slate-800 text-slate-400 border border-slate-700';
    }
  };

  const getEventBadge = (category, severity) => {
    switch (category) {
      case 'COMMUNICATION':
        return 'bg-blue-950/70 text-blue-400 border border-blue-800/60';
      case 'ASSIGNMENT':
        return 'bg-purple-950/70 text-purple-400 border border-purple-800/60';
      case 'COMPLETION':
        return 'bg-emerald-950/70 text-emerald-400 border border-emerald-800/60';
      case 'FAILURE':
        return 'bg-red-950/70 text-red-400 border border-red-800/60';
      case 'RECOVERY':
        return 'bg-orange-950/70 text-orange-400 border border-orange-800/60';
      default:
        return 'bg-slate-800 text-slate-300 border border-slate-700';
    }
  };

  return (
    <div className="space-y-6">
      {/* Alert Banners */}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-950/50 border border-red-500/40 text-red-300 text-sm flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-400" />
            <span>{errorMsg}</span>
          </div>
          <button onClick={() => setErrorMsg(null)} className="text-red-400 hover:text-white text-xs underline ml-4">
            Dismiss
          </button>
        </div>
      )}

      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-950/50 border border-emerald-500/40 text-emerald-300 text-sm flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-400" />
            <span>{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg(null)} className="text-emerald-400 hover:text-white text-xs underline ml-4">
            Dismiss
          </button>
        </div>
      )}

      {/* Primary Header with LIVE / SIMULATION STOPPED Indicators */}
      <div className="bg-gradient-to-r from-[#0d1b2a] via-[#0b132b] to-[#070d1e] border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              {/* Requirement: Clear LIVE / SIMULATION STOPPED indicator */}
              {isRunning ? (
                <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-bold bg-emerald-950/80 border border-emerald-500/60 text-emerald-300 shadow-lg shadow-emerald-950/40">
                  <span className="relative flex h-2.5 w-2.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
                  </span>
                  <span className="tracking-wider">LIVE</span>
                  <span className="text-[10px] text-emerald-400/80 font-mono">
                    ({connectionType === 'WEBSOCKET' ? 'WebSocket Streaming' : 'Live Polling'})
                  </span>
                </div>
              ) : (
                <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-bold bg-amber-950/80 border border-amber-500/60 text-amber-300 shadow-lg shadow-amber-950/40">
                  <Square className="w-3 h-3 fill-amber-400" />
                  <span className="tracking-wider">SIMULATION STOPPED</span>
                </div>
              )}

              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono text-slate-400 bg-slate-900 border border-slate-800">
                Tick: <strong className="text-white font-bold">{monitoringData?.current_tick ?? 0}</strong>
              </span>

              {lastUpdated && (
                <span className="text-[11px] text-slate-500 font-mono">
                  Updated {lastUpdated.toLocaleTimeString()}
                </span>
              )}
            </div>

            <h2 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight flex items-center space-x-2.5">
              <span>Real-Time Multi-Agent Monitoring Dashboard</span>
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 max-w-2xl leading-relaxed">
              Live operational oversight across Customer, Intake, Verification, Request Agent workers, Service pools, and
              Supervisor monitoring with actual backend telemetry.
            </p>
          </div>

          {/* Engine Action Controls */}
          <div className="flex flex-wrap items-center gap-3">
            {isRunning ? (
              <button
                onClick={handleStopSimulation}
                disabled={actionLoading}
                className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-bold bg-amber-500/20 border border-amber-500/50 text-amber-300 hover:bg-amber-500/30 transition shadow-lg disabled:opacity-50"
              >
                {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Square className="w-4 h-4" />}
                <span>Stop Engine</span>
              </button>
            ) : (
              <button
                onClick={handleStartSimulation}
                disabled={actionLoading}
                className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-lg transition disabled:opacity-50"
              >
                {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-white" />}
                <span>Start Simulation Engine</span>
              </button>
            )}

            <button
              onClick={fetchSnapshot}
              disabled={loading}
              className="inline-flex items-center space-x-2 px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
              title="Manual Telemetry Sync"
            >
              <RotateCw className={`w-4 h-4 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
              <span className="hidden sm:inline">Sync Now</span>
            </button>
          </div>
        </div>
      </div>

      {/* Requirement 9: Show total processed requests and failed requests (Metric Cards) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
        <div className="bg-[#0b132b] border border-slate-800 rounded-xl p-4 shadow-lg space-y-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Total Requests</span>
          <div className="text-2xl font-extrabold text-white font-mono">{metrics.total_requests}</div>
          <span className="text-[10px] text-slate-500 block truncate">PostgreSQL Registry</span>
        </div>

        <div className="bg-[#0b132b] border border-emerald-900/40 rounded-xl p-4 shadow-lg space-y-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-emerald-400">Processed (Done)</span>
          <div className="text-2xl font-extrabold text-emerald-400 font-mono">{metrics.processed_requests}</div>
          <span className="text-[10px] text-slate-500 block truncate">Completed Workflows</span>
        </div>

        <div className="bg-[#0b132b] border border-red-900/40 rounded-xl p-4 shadow-lg space-y-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-red-400">Failed Requests</span>
          <div className="text-2xl font-extrabold text-red-400 font-mono">{metrics.failed_requests}</div>
          <span className="text-[10px] text-slate-500 block truncate">Rejected / Failed</span>
        </div>

        <div className="bg-[#0b132b] border border-blue-900/40 rounded-xl p-4 shadow-lg space-y-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-blue-400">In-Flight Queue</span>
          <div className="text-2xl font-extrabold text-blue-400 font-mono">{metrics.pending_requests}</div>
          <span className="text-[10px] text-slate-500 block truncate">Active in Pipeline</span>
        </div>

        <div className="bg-[#0b132b] border border-cyan-900/40 rounded-xl p-4 shadow-lg space-y-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-cyan-400">Active Workers</span>
          <div className="text-2xl font-extrabold text-cyan-400 font-mono">{metrics.active_workers}</div>
          <span className="text-[10px] text-slate-500 block truncate">Busy Request Workers</span>
        </div>

        <div className="bg-[#0b132b] border border-slate-800 rounded-xl p-4 shadow-lg space-y-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Idle / Standby</span>
          <div className="text-2xl font-extrabold text-slate-300 font-mono">{metrics.idle_agents}</div>
          <span className="text-[10px] text-slate-500 block truncate">Available for Dispatch</span>
        </div>
      </div>

      {/* Requirements 1, 2, 3, 4, 5: Swarm Agent Hierarchy Cards */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-base font-bold text-white flex items-center space-x-2">
              <Cpu className="w-5 h-5 text-emerald-400" />
              <span>Multi-Agent Swarm Operational Topology</span>
            </h3>
            <p className="text-xs text-slate-400">
              Live status, actual database IDs, assigned requests, and processing stages for all agents.
            </p>
          </div>

          {/* Category Filter Tabs */}
          <div className="flex items-center space-x-1.5 bg-slate-900/80 border border-slate-800 p-1 rounded-xl text-xs">
            {['ALL', 'CORE', 'REQUEST', 'SERVICE'].map((cat) => (
              <button
                key={cat}
                onClick={() => setAgentCategoryFilter(cat)}
                className={`px-3 py-1 rounded-lg font-semibold transition ${
                  agentCategoryFilter === cat
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {cat === 'ALL' ? 'All Agents' : cat === 'CORE' ? 'Core Pipeline' : cat === 'REQUEST' ? 'Request Pool' : 'Service Pool'}
              </button>
            ))}
          </div>
        </div>

        {/* Agent Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {displayedAgents.map((agt) => (
            <div
              key={agt.agent_code}
              className="bg-[#0b132b] border border-slate-800 hover:border-slate-700 rounded-2xl p-4.5 shadow-xl transition-all space-y-3.5 flex flex-col justify-between"
            >
              {/* Header: Agent Code & ID */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-extrabold text-emerald-400 flex items-center space-x-1">
                    <Hash className="w-3.5 h-3.5 text-slate-500" />
                    <span>{agt.id ? `ID #${agt.id} • ` : ''}{agt.agent_code}</span>
                  </span>
                  <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold tracking-wider ${getStatusBadge(agt.status)}`}>
                    {agt.status}
                  </span>
                </div>
                <div className="text-sm font-bold text-white tracking-tight truncate">{agt.agent_name}</div>
                <div className="text-[11px] text-slate-400 font-mono">Role: {agt.agent_type}</div>
              </div>

              {/* Requirement 4 & 5: Assigned Request ID and Current Stage */}
              <div className="bg-[#070d1e] border border-slate-800/80 rounded-xl p-3 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-slate-400 font-medium">Assigned Request:</span>
                  {agt.current_request_id ? (
                    <span className="font-mono font-bold text-cyan-300 bg-cyan-950/60 border border-cyan-800/60 px-2 py-0.5 rounded text-[11px]">
                      {agt.current_request_id}
                    </span>
                  ) : (
                    <span className="text-slate-500 italic text-[11px]">None (Standby)</span>
                  )}
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-slate-400 font-medium">Processing Stage:</span>
                  <span
                    className={`font-mono text-[11px] font-bold px-2 py-0.5 rounded ${
                      agt.current_stage === 'IDLE'
                        ? 'text-slate-400 bg-slate-900 border border-slate-800'
                        : 'text-emerald-400 bg-emerald-950/60 border border-emerald-800/60'
                    }`}
                  >
                    {agt.current_stage}
                  </span>
                </div>

                {agt.supported_skills && agt.supported_skills.length > 0 && (
                  <div className="pt-1 flex flex-wrap gap-1">
                    {agt.supported_skills.map((sk) => (
                      <span key={sk} className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {sk}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Footer: Health & Completed Tasks */}
              <div className="flex items-center justify-between text-[11px] pt-1 border-t border-slate-800/60 text-slate-400">
                <span>Health: <strong className={agt.health_status === 'HEALTHY' ? 'text-emerald-400' : 'text-amber-400'}>{agt.health_status}</strong></span>
                <span>Resolved: <strong className="text-white font-mono">{agt.completed_tasks}</strong></span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Requirement 6, 7, 8, 13: Live Event Log with Timestamps */}
      <div className="bg-[#0b132b] border border-slate-800 rounded-2xl shadow-xl p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div>
            <h3 className="text-base font-bold text-white flex items-center space-x-2">
              <Terminal className="w-5 h-5 text-emerald-400" />
              <span>Live Agent Event Stream & Audit Trail</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Real-time feed of communication exchanges, task assignments, fulfillments, failures, and recoveries.
            </p>
          </div>

          {/* Event Filter */}
          <div className="flex flex-wrap items-center gap-1.5 bg-slate-900/80 border border-slate-800 p-1 rounded-xl text-xs">
            {['ALL', 'COMMUNICATION', 'ASSIGNMENT', 'COMPLETION', 'FAILURE', 'RECOVERY'].map((cat) => (
              <button
                key={cat}
                onClick={() => setEventCategoryFilter(cat)}
                className={`px-2.5 py-1 rounded-lg font-semibold transition ${
                  eventCategoryFilter === cat
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Live Stream Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-[#0d1733] text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Sender Agent</th>
                <th className="py-3 px-4">Receiver / Target</th>
                <th className="py-3 px-4">Request ID</th>
                <th className="py-3 px-4">Event Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/70 text-slate-200">
              {displayedEvents.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500">
                    No matching events recorded in the live stream yet.
                  </td>
                </tr>
              ) : (
                displayedEvents.map((ev, idx) => (
                  <tr key={ev.event_id || idx} className="hover:bg-slate-900/40 transition-colors">
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-400 whitespace-nowrap">
                      {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : '—'}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase ${getEventBadge(ev.category, ev.severity)}`}>
                        {ev.category}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono font-bold text-emerald-400 whitespace-nowrap">
                      {ev.sender}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300 whitespace-nowrap">
                      {ev.receiver || <span className="text-slate-600">—</span>}
                    </td>
                    <td className="py-3 px-4 font-mono text-cyan-300 font-semibold whitespace-nowrap">
                      {ev.request_id || <span className="text-slate-600">—</span>}
                    </td>
                    <td className="py-3 px-4 text-slate-300 max-w-md truncate">
                      {ev.message}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Controlled Scenario Benchmark Runner */}
      <div className="bg-[#0b132b] border border-slate-800 rounded-2xl shadow-xl p-6 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 gap-3">
          <div>
            <h3 className="text-base font-bold text-white flex items-center space-x-2">
              <BarChart2 className="w-5 h-5 text-emerald-400" />
              <span>Demonstration Workloads & Concurrency Benchmarks</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Submit synthetic concurrent batches to demonstrate multi-agent parallel dispatch and verification.
            </p>
          </div>
          <button
            onClick={handleRunScenario}
            disabled={scenarioLoading}
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-lg transition disabled:opacity-50"
          >
            {scenarioLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-white" />}
            <span>Run Benchmark Workflow</span>
          </button>
        </div>

        {/* Scenario Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {[
            { id: 1, title: 'Scenario 1: Normal Processing', badge: '20 Requests / 3 Workers', desc: 'Valid requests processed across concurrent Request Agents.' },
            { id: 2, title: 'Scenario 2: Concurrent Stress Test', badge: '60 Requests / 5 Workers', desc: 'Burst load proving concurrent worker task distribution.' },
            { id: 3, title: 'Scenario 3: Validation Exceptions', badge: '20 Requests / 50% Incomplete', desc: 'Evaluates NEEDS_CORRECTION routing on invalid customer input.' },
            { id: 4, title: 'Scenario 4: Mixed Service Types', badge: '24 Requests / 4 Services', desc: 'Concurrent dispatch to specialized service sub-agents.' },
            { id: 5, title: 'Scenario 5: Human Supervisory Review', badge: '20 Requests / Security & KYC', desc: 'Routes complex requests to staff review gates.' },
          ].map((sc) => (
            <div
              key={sc.id}
              onClick={() => setSelectedScenario(sc.id)}
              className={`cursor-pointer rounded-xl p-4 border transition-all space-y-2 ${
                selectedScenario === sc.id
                  ? 'bg-emerald-950/30 border-emerald-500/60 shadow-md ring-1 ring-emerald-500/30'
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white">{sc.title}</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-emerald-400 border border-slate-700">
                  {sc.badge}
                </span>
              </div>
              <p className="text-[11px] text-slate-300 leading-relaxed">{sc.desc}</p>
            </div>
          ))}
        </div>

        {/* Scenario Result Preview */}
        {scenarioResult && (
          <div className="mt-4 bg-[#0d1733] border border-emerald-800/50 rounded-xl p-5 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-3 gap-2">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <span className="font-bold text-white text-sm">
                  {scenarioResult.scenario_name} Completed
                </span>
              </div>
              <div className="flex items-center space-x-4 text-xs">
                <span className="text-slate-400">
                  Duration: <strong className="text-white">{scenarioResult.duration_seconds}s</strong>
                </span>
                <span className="text-slate-400">
                  Peak Concurrency: <strong className="text-emerald-400">{scenarioResult.peak_concurrency} active workers</strong>
                </span>
              </div>
            </div>

            <div className="flex flex-wrap gap-2 pt-1">
              {Object.entries(scenarioResult.status_breakdown || {}).map(([st, cnt]) => (
                <span
                  key={st}
                  className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-bold bg-slate-900 border border-slate-700 text-slate-200"
                >
                  <span className="text-slate-400">{st}:</span>
                  <span className="text-emerald-400">{cnt}</span>
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
