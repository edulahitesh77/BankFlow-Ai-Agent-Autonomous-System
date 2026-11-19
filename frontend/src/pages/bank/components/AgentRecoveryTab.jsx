import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Activity,
  AlertTriangle,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock,
  Play,
  Pause,
  RotateCcw,
  Sliders,
  ChevronDown,
  ChevronUp,
  Zap,
  Radio,
  Server,
  ArrowRight,
} from 'lucide-react';
import {
  fetchRecoveryDashboard,
  triggerHealthInspection,
  manualRetryTask,
  manualReassignTask,
  resetAgentHealth,
  pauseAgent,
  resumeAgent,
  resetCircuitBreaker,
  simulateAgentCrash,
  simulateMissedHeartbeat,
  simulateRabbitMQOutage,
  simulateRabbitMQRestore,
  simulateRetryExhaustion,
} from '../../../api/auth';

export const AgentRecoveryTab = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);
  const [showChaosPanel, setShowChaosPanel] = useState(false);

  // Manual Reassignment Modal State
  const [reassignModalOpen, setReassignModalOpen] = useState(false);
  const [targetRequestId, setTargetRequestId] = useState('');
  const [targetAgentCode, setTargetAgentCode] = useState('RequestAgent_1');

  // Chaos Simulation State
  const [chaosAgentCode, setChaosAgentCode] = useState('RequestAgent_2');
  const [chaosRequestId, setChaosRequestId] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await fetchRecoveryDashboard();
      setData(res);
    } catch (err) {
      setStatusMessage({ type: 'error', text: err.message || 'Failed to load recovery dashboard.' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000); // 10s auto refresh
    return () => clearInterval(interval);
  }, []);

  const handleInspectHealth = async () => {
    try {
      setActionLoading(true);
      const res = await triggerHealthInspection();
      setStatusMessage({
        type: 'success',
        text: `Health inspection completed: ${res.unresponsive_detected} unresponsive agents, ${res.recovered_tasks} tasks recovered.`,
      });
      await loadData();
    } catch (err) {
      setStatusMessage({ type: 'error', text: err.message || 'Inspection failed.' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleRetry = async (reqCode) => {
    if (!reqCode) return;
    try {
      setActionLoading(true);
      const res = await manualRetryTask(reqCode);
      setStatusMessage({
        type: 'success',
        text: `Task '${reqCode}' successfully retried: ${res.recovery_result?.status || 'Initiated'}.`,
      });
      await loadData();
    } catch (err) {
      setStatusMessage({ type: 'error', text: err.message || 'Retry failed.' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleResetAgent = async (agentCode) => {
    try {
      setActionLoading(true);
      await resetAgentHealth(agentCode);
      setStatusMessage({
        type: 'success',
        text: `Agent '${agentCode}' health status reset to HEALTHY.`,
      });
      await loadData();
    } catch (err) {
      setStatusMessage({ type: 'error', text: err.message || 'Failed to reset agent.' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleTogglePause = async (agentCode, currentlyPaused) => {
    try {
      setActionLoading(true);
      if (currentlyPaused) {
        await resumeAgent(agentCode);
        setStatusMessage({ type: 'success', text: `Agent '${agentCode}' resumed.` });
      } else {
        await pauseAgent(agentCode);
        setStatusMessage({ type: 'success', text: `Agent '${agentCode}' paused.` });
      }
      await loadData();
    } catch (err) {
      setStatusMessage({ type: 'error', text: err.message || 'Pause/resume failed.' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleResetCircuitBreaker = async () => {
    try {
      setActionLoading(true);
      await resetCircuitBreaker();
      setStatusMessage({ type: 'success', text: 'Circuit Breaker manually reset to CLOSED.' });
      await loadData();
    } catch (err) {
      setStatusMessage({ type: 'error', text: err.message || 'Reset failed.' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleReassignSubmit = async (e) => {
    e.preventDefault();
    try {
      setActionLoading(true);
      await manualReassignTask(targetRequestId, targetAgentCode);
      setStatusMessage({
        type: 'success',
        text: `Request '${targetRequestId}' reassigned to '${targetAgentCode}'.`,
      });
      setReassignModalOpen(false);
      await loadData();
    } catch (err) {
      setStatusMessage({ type: 'error', text: err.message || 'Reassignment failed.' });
    } finally {
      setActionLoading(false);
    }
  };

  // Chaos simulations
  const handleSimulateCrash = async () => {
    try {
      setActionLoading(true);
      await simulateAgentCrash(chaosAgentCode, 'Simulated worker memory crash');
      setStatusMessage({ type: 'warning', text: `Simulated crash induced on agent '${chaosAgentCode}'.` });
      await loadData();
    } catch (err) {
      setStatusMessage({ type: 'error', text: err.message });
    } finally {
      setActionLoading(false);
    }
  };

  const handleSimulateMissedHeartbeat = async () => {
    try {
      setActionLoading(true);
      await simulateMissedHeartbeat(chaosAgentCode, 60.0);
      setStatusMessage({ type: 'warning', text: `Agent '${chaosAgentCode}' heartbeat set 60s in the past.` });
      await loadData();
    } catch (err) {
      setStatusMessage({ type: 'error', text: err.message });
    } finally {
      setActionLoading(false);
    }
  };

  const handleSimulateBrokerOutage = async () => {
    try {
      setActionLoading(true);
      await simulateRabbitMQOutage();
      setStatusMessage({ type: 'warning', text: 'RabbitMQ Circuit Breaker tripped to OPEN.' });
      await loadData();
    } catch (err) {
      setStatusMessage({ type: 'error', text: err.message });
    } finally {
      setActionLoading(false);
    }
  };

  const handleSimulateBrokerRestore = async () => {
    try {
      setActionLoading(true);
      await simulateRabbitMQRestore();
      setStatusMessage({ type: 'success', text: 'RabbitMQ Circuit Breaker restored to CLOSED.' });
      await loadData();
    } catch (err) {
      setStatusMessage({ type: 'error', text: err.message });
    } finally {
      setActionLoading(false);
    }
  };

  const handleSimulateRetryExhaustion = async () => {
    if (!chaosRequestId) {
      setStatusMessage({ type: 'error', text: 'Please enter a Request ID for retry exhaustion test.' });
      return;
    }
    try {
      setActionLoading(true);
      const res = await simulateRetryExhaustion(chaosRequestId);
      setStatusMessage({
        type: 'warning',
        text: `Retry limit exhausted for '${chaosRequestId}'. Escalated to: ${res.final_status}.`,
      });
      await loadData();
    } catch (err) {
      setStatusMessage({ type: 'error', text: err.message });
    } finally {
      setActionLoading(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="flex justify-center items-center py-24">
        <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  const { agents_summary, requests_summary, circuit_breaker, recent_failures } = data || {};

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Header Banner */}
      <div className="bg-slate-900 text-white rounded-3xl p-6 sm:p-8 shadow-xl relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 w-96 bg-gradient-to-l from-emerald-500/10 to-transparent pointer-events-none" />
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 relative z-10">
          <div>
            <div className="flex items-center space-x-3">
              <span className="p-2 bg-emerald-500/20 text-emerald-400 rounded-xl">
                <ShieldAlert className="w-6 h-6" />
              </span>
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight">Agent Recovery & Fault Tolerance</h2>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-2xl">
              Phase 8 autonomous self-healing coordinator. Monitors agent heartbeats, recovers abandoned tasks,
              prevents duplicate execution, and enforces circuit protection.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleInspectHealth}
              disabled={actionLoading}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold shadow-md transition flex items-center space-x-2 disabled:opacity-60"
            >
              <Activity className="w-4 h-4" />
              <span>Inspect Health</span>
            </button>
            <button
              onClick={loadData}
              disabled={loading}
              className="p-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold border border-slate-700 transition"
              title="Refresh"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Circuit Breaker Status Banner */}
        {circuit_breaker && (
          <div className="mt-6 pt-6 border-t border-slate-800 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center space-x-3">
              <span className="text-xs text-slate-400">RabbitMQ Circuit Breaker:</span>
              <span
                className={`px-3 py-1 rounded-full text-xs font-extrabold uppercase tracking-wider ${
                  circuit_breaker.state === 'CLOSED'
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : circuit_breaker.state === 'HALF_OPEN'
                    ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    : 'bg-rose-500/20 text-rose-400 border border-rose-500/30 animate-pulse'
                }`}
              >
                ● {circuit_breaker.state}
              </span>
              <span className="text-xs text-slate-400">
                Failures: {circuit_breaker.failure_count}/{circuit_breaker.failure_threshold}
              </span>
            </div>

            {circuit_breaker.state !== 'CLOSED' && (
              <button
                onClick={handleResetCircuitBreaker}
                disabled={actionLoading}
                className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold transition"
              >
                Reset to CLOSED
              </button>
            )}
          </div>
        )}
      </div>

      {/* Status Alert Toast */}
      {statusMessage && (
        <div
          className={`p-4 rounded-2xl border text-xs flex items-center justify-between animate-fade-in ${
            statusMessage.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : statusMessage.type === 'warning'
              ? 'bg-amber-50 border-amber-200 text-amber-900'
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}
        >
          <div className="flex items-center space-x-2">
            {statusMessage.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-amber-600" />
            )}
            <span>{statusMessage.text}</span>
          </div>
          <button
            onClick={() => setStatusMessage(null)}
            className="text-slate-400 hover:text-slate-600 font-bold ml-4"
          >
            ×
          </button>
        </div>
      )}

      {/* KPI Overview Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm text-center">
          <div className="text-xs text-slate-500 font-medium">Total Agents</div>
          <div className="text-2xl font-extrabold text-slate-900 mt-1">{agents_summary?.total ?? 0}</div>
        </div>
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm text-center">
          <div className="text-xs text-emerald-600 font-medium">Healthy</div>
          <div className="text-2xl font-extrabold text-emerald-600 mt-1">{agents_summary?.healthy ?? 0}</div>
        </div>
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm text-center">
          <div className="text-xs text-blue-600 font-medium">Busy Working</div>
          <div className="text-2xl font-extrabold text-blue-600 mt-1">{agents_summary?.busy ?? 0}</div>
        </div>
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm text-center">
          <div className="text-xs text-amber-600 font-medium">Unresponsive</div>
          <div className="text-2xl font-extrabold text-amber-600 mt-1">{agents_summary?.unresponsive ?? 0}</div>
        </div>
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm text-center">
          <div className="text-xs text-rose-600 font-medium">Failed</div>
          <div className="text-2xl font-extrabold text-rose-600 mt-1">{agents_summary?.failed ?? 0}</div>
        </div>
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm text-center">
          <div className="text-xs text-purple-600 font-medium">Recovered Tasks</div>
          <div className="text-2xl font-extrabold text-purple-600 mt-1">
            {requests_summary?.successfully_recovered ?? 0}
          </div>
        </div>
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm text-center">
          <div className="text-xs text-orange-600 font-medium">Human Review</div>
          <div className="text-2xl font-extrabold text-orange-600 mt-1">
            {requests_summary?.human_intervention_needed ?? 0}
          </div>
        </div>
      </div>

      {/* Recent Failure Events & Automated Recovery History Table */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <div>
            <h3 className="text-base font-bold text-slate-900">Failure Registry & Recovery History</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Traceable record of agent crashes, heartbeat timeouts, broker exceptions, and automatic reassignments.
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => {
                setTargetRequestId('');
                setReassignModalOpen(true);
              }}
              className="px-3.5 py-2 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-xl text-xs font-semibold transition"
            >
              Manual Reassign
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 text-slate-600 uppercase tracking-wider font-semibold border-b border-slate-200">
                <th className="py-3 px-4">Failure ID</th>
                <th className="py-3 px-4">Agent</th>
                <th className="py-3 px-4">Request</th>
                <th className="py-3 px-4">Failure Type</th>
                <th className="py-3 px-4">Sanitized Details</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Retries</th>
                <th className="py-3 px-4">Recorded At</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {recent_failures && recent_failures.length > 0 ? (
                recent_failures.map((f) => (
                  <tr key={f.failure_id} className="hover:bg-slate-50 transition">
                    <td className="py-3.5 px-4 font-mono font-bold text-slate-800">{f.failure_id}</td>
                    <td className="py-3.5 px-4 font-medium text-slate-700">{f.agent_code || '—'}</td>
                    <td className="py-3.5 px-4 font-mono text-blue-600 font-semibold">{f.request_code || '—'}</td>
                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded font-mono text-[10px] font-bold">
                        {f.failure_type}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 max-w-xs truncate text-slate-500" title={f.error_details}>
                      {f.error_details || '—'}
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase ${
                          f.recovery_status === 'RECOVERED'
                            ? 'bg-emerald-100 text-emerald-800'
                            : f.recovery_status === 'ESCALATED_TO_HUMAN'
                            ? 'bg-orange-100 text-orange-800'
                            : f.recovery_status === 'RECOVERING'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-rose-100 text-rose-800'
                        }`}
                      >
                        {f.recovery_status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-mono">{f.retry_count}</td>
                    <td className="py-3.5 px-4 text-slate-400">
                      {f.created_at ? new Date(f.created_at).toLocaleTimeString() : '—'}
                    </td>
                    <td className="py-3.5 px-4 text-right space-x-1">
                      {f.request_code && f.recovery_status !== 'RECOVERED' && (
                        <button
                          onClick={() => handleRetry(f.request_code)}
                          disabled={actionLoading}
                          className="px-2 py-1 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded text-[11px] font-semibold transition"
                          title="Retry Request"
                        >
                          Retry
                        </button>
                      )}
                      {f.agent_code && (
                        <button
                          onClick={() => handleResetAgent(f.agent_code)}
                          disabled={actionLoading}
                          className="px-2 py-1 bg-slate-100 text-slate-700 hover:bg-slate-200 rounded text-[11px] font-semibold transition"
                          title="Reset Agent"
                        >
                          Reset
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-400 text-xs">
                    No failure events recorded. All agents operating within nominal tolerances.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Failure Simulation & Chaos Testing Panel */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        <button
          onClick={() => setShowChaosPanel(!showChaosPanel)}
          className="w-full p-6 text-left flex justify-between items-center hover:bg-slate-50 transition"
        >
          <div className="flex items-center space-x-3">
            <span className="p-2 bg-amber-100 text-amber-700 rounded-xl">
              <Zap className="w-5 h-5" />
            </span>
            <div>
              <h3 className="text-base font-bold text-slate-900">Chaos Engineering & Failure Simulation Harness</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Authorized development tools to inject agent crashes, missed heartbeats, broker blips, and retry exhaustion.
              </p>
            </div>
          </div>
          {showChaosPanel ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
        </button>

        {showChaosPanel && (
          <div className="p-6 border-t border-slate-100 bg-slate-50/50 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Chaos Scenario 1: Agent Crash */}
              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
                <div className="font-bold text-xs text-slate-900 flex items-center space-x-2">
                  <XCircle className="w-4 h-4 text-rose-500" />
                  <span>Simulate Agent Crash</span>
                </div>
                <p className="text-[11px] text-slate-500">
                  Forces an agent into FAILED status to verify task reassignment.
                </p>
                <input
                  type="text"
                  value={chaosAgentCode}
                  onChange={(e) => setChaosAgentCode(e.target.value)}
                  placeholder="Agent Code (e.g. RequestAgent_2)"
                  className="w-full px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-mono"
                />
                <button
                  onClick={handleSimulateCrash}
                  disabled={actionLoading}
                  className="w-full py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-semibold shadow-sm transition"
                >
                  Induce Agent Crash
                </button>
              </div>

              {/* Chaos Scenario 2: Missed Heartbeat */}
              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
                <div className="font-bold text-xs text-slate-900 flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-amber-500" />
                  <span>Simulate Missed Heartbeat</span>
                </div>
                <p className="text-[11px] text-slate-500">
                  Pushes an agent's heartbeat timestamp 60s in the past to trigger timeout.
                </p>
                <button
                  onClick={handleSimulateMissedHeartbeat}
                  disabled={actionLoading}
                  className="w-full py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-semibold shadow-sm transition mt-7"
                >
                  Induce Heartbeat Stale
                </button>
              </div>

              {/* Chaos Scenario 3: RabbitMQ Circuit Outage */}
              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
                <div className="font-bold text-xs text-slate-900 flex items-center space-x-2">
                  <Radio className="w-4 h-4 text-blue-500" />
                  <span>Broker Circuit Breaker</span>
                </div>
                <p className="text-[11px] text-slate-500">
                  Trips or restores the RabbitMQ circuit breaker without restarting processes.
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={handleSimulateBrokerOutage}
                    disabled={actionLoading}
                    className="flex-1 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-xl text-xs font-semibold shadow-sm transition"
                  >
                    Trip Circuit (OPEN)
                  </button>
                  <button
                    onClick={handleSimulateBrokerRestore}
                    disabled={actionLoading}
                    className="flex-1 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold shadow-sm transition"
                  >
                    Restore (CLOSED)
                  </button>
                </div>
              </div>
            </div>

            {/* Chaos Scenario 4: Retry Exhaustion */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3 max-w-md">
              <div className="font-bold text-xs text-slate-900 flex items-center space-x-2">
                <RotateCcw className="w-4 h-4 text-purple-500" />
                <span>Simulate Retry Exhaustion & Human Escalation</span>
              </div>
              <p className="text-[11px] text-slate-500">
                Pushes retry counter to 3 and triggers recovery to test transition into HUMAN_REVIEW.
              </p>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={chaosRequestId}
                  onChange={(e) => setChaosRequestId(e.target.value)}
                  placeholder="Request ID (e.g. BFA-REQ-2026-00001)"
                  className="flex-1 px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-mono"
                />
                <button
                  onClick={handleSimulateRetryExhaustion}
                  disabled={actionLoading}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-semibold shadow-sm transition"
                >
                  Exhaust Retries
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Manual Task Reassign Modal */}
      {reassignModalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 sm:p-8 space-y-5 shadow-2xl animate-fade-in">
            <div>
              <h3 className="text-lg font-bold text-slate-900">Manual Task Reassignment</h3>
              <p className="text-xs text-slate-500 mt-1">
                Atomically releases existing assignment and re-binds request to another healthy worker.
              </p>
            </div>

            <form onSubmit={handleReassignSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Target Request ID</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. BFA-REQ-2026-00001"
                  value={targetRequestId}
                  onChange={(e) => setTargetRequestId(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Assign to Agent</label>
                <select
                  value={targetAgentCode}
                  onChange={(e) => setTargetAgentCode(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="RequestAgent_1">RequestAgent_1</option>
                  <option value="RequestAgent_2">RequestAgent_2</option>
                  <option value="RequestAgent_3">RequestAgent_3</option>
                </select>
              </div>

              <div className="flex gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setReassignModalOpen(false)}
                  className="flex-1 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold shadow-md transition disabled:opacity-60"
                >
                  {actionLoading ? 'Reassigning...' : 'Confirm Reassign'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
