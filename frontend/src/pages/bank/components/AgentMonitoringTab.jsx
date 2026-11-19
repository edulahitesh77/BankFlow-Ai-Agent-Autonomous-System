import React, { useState, useEffect, useCallback } from 'react';
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
  HelpCircle,
  ArrowRight,
} from 'lucide-react';
import {
  fetchBankAgents,
  fetchAgentStatistics,
  fetchSimulationStatus,
  startSimulation,
  stopSimulation,
  runSimulationScenario,
} from '../../../api/auth';

export const AgentMonitoringTab = () => {
  const [agents, setAgents] = useState([]);
  const [agentStats, setAgentStats] = useState(null);
  const [simStatus, setSimStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [scenarioLoading, setScenarioLoading] = useState(false);
  const [selectedScenario, setSelectedScenario] = useState(1);
  const [scenarioResult, setScenarioResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  const loadData = useCallback(async () => {
    try {
      const [agentsData, statsData, statusData] = await Promise.all([
        fetchBankAgents(),
        fetchAgentStatistics().catch(() => null),
        fetchSimulationStatus().catch(() => null),
      ]);
      setAgents(agentsData.agents || []);
      setAgentStats(statsData);
      setSimStatus(statusData);
      setErrorMsg(null);
    } catch (err) {
      console.error('Failed to load agent monitoring data:', err);
      setErrorMsg(err.message || 'Failed to communicate with multi-agent system.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    // Auto refresh every 5 seconds if simulation is active
    const interval = setInterval(() => {
      loadData();
    }, 5000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleStartSimulation = async () => {
    setActionLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      await startSimulation({
        num_request_agents: 3,
        tick_delay_seconds: 0.5,
        scenario_name: 'MANUAL_SUPERVISED',
      });
      setSuccessMsg('Simulation engine started successfully.');
      await loadData();
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
      await loadData();
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
      await loadData();
    } catch (err) {
      setErrorMsg(err.message || 'Failed to execute benchmark scenario.');
    } finally {
      setScenarioLoading(false);
    }
  };

  const isRunning = simStatus?.is_running || false;

  const scenariosList = [
    {
      id: 1,
      title: 'Scenario 1: Normal Processing',
      badge: '20 Requests / 3 Workers',
      desc: 'Valid cheque book and debit card requests processed smoothly through the full lifecycle to completion.',
    },
    {
      id: 2,
      title: 'Scenario 2: Increased Load Stress Test',
      badge: '60 Requests / 5 Workers',
      desc: 'High request arrival rate demonstrating concurrency distribution across 5 Request Agents.',
    },
    {
      id: 3,
      title: 'Scenario 3: Incomplete Requests (Corrections)',
      badge: '20 Requests / 50% Incomplete',
      desc: 'Tests field validation triggers: missing leaves or invalid addresses transition to NEEDS_CORRECTION.',
    },
    {
      id: 4,
      title: 'Scenario 4: Mixed Service Types',
      badge: '24 Requests / 4 Services',
      desc: 'All 4 service categories distributed to specialized Service Agents in parallel.',
    },
    {
      id: 5,
      title: 'Scenario 5: Human Supervisory Gate',
      badge: '20 Requests / Security & KYC',
      desc: 'Lost card replacements and new account pre-screenings routed strictly to HUMAN_REVIEW.',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Alert Banners */}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-500/40 text-red-300 text-sm flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-400" />
            <span>{errorMsg}</span>
          </div>
          <button
            onClick={() => setErrorMsg(null)}
            className="text-red-400 hover:text-white text-xs underline ml-4"
          >
            Dismiss
          </button>
        </div>
      )}

      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-sm flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-400" />
            <span>{successMsg}</span>
          </div>
          <button
            onClick={() => setSuccessMsg(null)}
            className="text-emerald-400 hover:text-white text-xs underline ml-4"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Top Engine Overview & Controls */}
      <div className="bg-gradient-to-r from-emerald-950/40 via-[#0d1733] to-[#0b132b] border border-emerald-800/60 rounded-2xl p-6 sm:p-8 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              <Cpu className="w-4 h-4" />
              <span>Phase 5 Multi-Agent System Active</span>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse ml-1" />
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
              Intelligent Multi-Agent Swarm Orchestration
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 max-w-2xl leading-relaxed">
              Mesa-driven agent modeling coordinating Customer, Intake, Verification, Request, and Service
              agents with strict auditable state machine transitions.
            </p>
          </div>

          <div className="flex items-center space-x-3">
            {isRunning ? (
              <button
                onClick={handleStopSimulation}
                disabled={actionLoading}
                className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold bg-amber-500/20 border border-amber-500/40 text-amber-300 hover:bg-amber-500/30 transition-all shadow-md"
              >
                {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Square className="w-4 h-4" />}
                <span>Stop Engine</span>
              </button>
            ) : (
              <button
                onClick={handleStartSimulation}
                disabled={actionLoading}
                className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/30 transition-all shadow-md"
              >
                {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                <span>Start Engine</span>
              </button>
            )}

            <button
              onClick={loadData}
              disabled={loading}
              className="inline-flex items-center space-x-2 px-3 py-2 rounded-xl text-xs font-semibold bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all"
              title="Refresh Swarm Telemetry"
            >
              <RotateCw className={`w-4 h-4 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
              <span className="hidden sm:inline">Refresh</span>
            </button>
          </div>
        </div>

        {/* Engine Status Indicators */}
        <div className="pt-2 flex flex-wrap items-center gap-3 text-xs">
          <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-slate-300">
            <span className="text-slate-500">Engine State:</span>
            <span
              className={`font-bold ${
                isRunning ? 'text-emerald-400 flex items-center gap-1.5' : 'text-slate-400'
              }`}
            >
              {isRunning && <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />}
              {isRunning ? 'RUNNING (Ticks Active)' : 'STANDBY / IDLE'}
            </span>
          </div>

          <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-slate-300">
            <span className="text-slate-500">Current Tick:</span>
            <span className="font-mono font-bold text-white">{simStatus?.current_tick ?? 0}</span>
          </div>

          <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-slate-300">
            <span className="text-slate-500">Active Workers:</span>
            <span className="font-mono font-bold text-emerald-400">
              {simStatus?.active_workers ?? 0}
            </span>
          </div>
        </div>
      </div>

      {/* Metric Telemetry Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-[#0b132b] border border-slate-800 rounded-2xl p-5 shadow-lg space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Agents</span>
            <Users className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {agentStats?.total_agents ?? agents.length}
          </div>
          <div className="text-[11px] text-slate-400">Registered Swarm Instances</div>
        </div>

        <div className="bg-[#0b132b] border border-slate-800 rounded-2xl p-5 shadow-lg space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Available Agents</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400">
            {agentStats?.available_agents ?? agents.filter((a) => a.availability_status === 'AVAILABLE').length}
          </div>
          <div className="text-[11px] text-slate-400">Ready for Task Dispatch</div>
        </div>

        <div className="bg-[#0b132b] border border-slate-800 rounded-2xl p-5 shadow-lg space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Busy Workers</span>
            <Activity className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400">
            {agentStats?.busy_agents ?? agents.filter((a) => a.availability_status === 'BUSY').length}
          </div>
          <div className="text-[11px] text-slate-400">Executing Assigned Requests</div>
        </div>

        <div className="bg-[#0b132b] border border-slate-800 rounded-2xl p-5 shadow-lg space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Tasks Resolved</span>
            <Zap className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-blue-400">
            {agentStats?.total_requests_processed ??
              agents.reduce((acc, a) => acc + (a.completed_work_count || 0), 0)}
          </div>
          <div className="text-[11px] text-slate-400">Fulfillments Completed</div>
        </div>
      </div>

      {/* Scenario Benchmark Control Panel */}
      <div className="bg-[#0b132b] border border-slate-800 rounded-2xl shadow-xl p-6 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 gap-3">
          <div>
            <h3 className="text-base font-bold text-white flex items-center space-x-2">
              <BarChart2 className="w-5 h-5 text-emerald-400" />
              <span>Multi-Agent Scenario Benchmarks (Controlled Testing)</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Execute deterministic simulation workloads to evaluate concurrency, validation, and human review routing.
            </p>
          </div>
          <button
            onClick={handleRunScenario}
            disabled={scenarioLoading}
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-lg transition-all disabled:opacity-50"
          >
            {scenarioLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4 fill-white" />
            )}
            <span>Run Selected Benchmark</span>
          </button>
        </div>

        {/* Scenario Selection Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {scenariosList.map((sc) => (
            <div
              key={sc.id}
              onClick={() => setSelectedScenario(sc.id)}
              className={`cursor-pointer rounded-xl p-4 border transition-all text-left space-y-2 ${
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

        {/* Scenario Results Viewer */}
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

            {/* Status Breakdown Pills */}
            <div className="space-y-1.5">
              <span className="text-[11px] font-semibold uppercase text-slate-400 tracking-wider">
                Request Status Breakdown
              </span>
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

            {/* Execution Log Terminal */}
            <div className="space-y-1.5">
              <span className="text-[11px] font-semibold uppercase text-slate-400 tracking-wider flex items-center space-x-1.5">
                <Terminal className="w-3.5 h-3.5 text-slate-400" />
                <span>Simulation Tick Logs</span>
              </span>
              <div className="bg-[#070d1e] border border-slate-800/80 rounded-lg p-3 font-mono text-[11px] text-slate-300 max-h-48 overflow-y-auto space-y-1">
                {scenarioResult.execution_logs?.map((log, idx) => (
                  <div key={idx} className="flex items-start space-x-2">
                    <span className="text-slate-600 select-none">[{String(idx + 1).padStart(2, '0')}]</span>
                    <span className="text-emerald-300/90">{log}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Live Swarm Agent Registry Table */}
      <div className="bg-[#0b132b] border border-slate-800 rounded-2xl shadow-xl p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <h3 className="text-base font-bold text-white flex items-center space-x-2">
              <Layers className="w-5 h-5 text-emerald-400" />
              <span>Multi-Agent Swarm Registry (Live Roster)</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Live operational agents registered in PostgreSQL and running in the Mesa simulation model.
            </p>
          </div>
          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950/60 border border-emerald-500/40 text-emerald-400">
            {agents.length} Active Agents
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-[#0d1733] text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                <th className="py-3 px-4">Agent Code</th>
                <th className="py-3 px-4">Role Type</th>
                <th className="py-3 px-4">Availability</th>
                <th className="py-3 px-4">Processing State</th>
                <th className="py-3 px-4">Current Request</th>
                <th className="py-3 px-4 text-right">Tasks Completed</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 text-slate-200">
              {loading && agents.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-emerald-400" />
                    <span>Loading agent registry...</span>
                  </td>
                </tr>
              ) : agents.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500">
                    No agents currently registered in the database.
                  </td>
                </tr>
              ) : (
                agents.map((agent, idx) => (
                  <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-emerald-400">
                      {agent.agent_code}
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
                        {agent.agent_type}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          agent.availability_status === 'AVAILABLE'
                            ? 'bg-emerald-950/70 text-emerald-400 border border-emerald-800'
                            : agent.availability_status === 'BUSY'
                            ? 'bg-amber-950/70 text-amber-400 border border-amber-800'
                            : 'bg-slate-800 text-slate-400 border border-slate-700'
                        }`}
                      >
                        {agent.availability_status}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-300">
                      {agent.processing_status || 'IDLE'}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-400">
                      {agent.current_request_id ? (
                        <span className="text-emerald-300 font-bold">{agent.current_request_id}</span>
                      ) : (
                        <span className="text-slate-600 italic">None (Standby)</span>
                      )}
                    </td>
                    <td className="py-3 px-4 font-mono font-bold text-white text-right">
                      {agent.completed_work_count ?? 0}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
