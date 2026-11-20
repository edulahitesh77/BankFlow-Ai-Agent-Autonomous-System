import React, { useState, useEffect, useCallback } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  RotateCw,
  Play,
  Pause,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  Radio,
  Database,
  ArrowRight,
  Layers,
  Terminal,
  Activity,
  Zap,
} from 'lucide-react';

import {
  fetchVisualizerRecoverySequence,
  simulateVisualizerRecovery,
} from '../../../../api/auth';

export const FailureRecoveryView = () => {
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [activeSequence, setActiveSequence] = useState(null);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(false);

  const loadRecoveryHistory = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchVisualizerRecoverySequence();
      setHistory(data);
    } catch (err) {
      console.error('Failed to load recovery history:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRecoveryHistory();
  }, [loadRecoveryHistory]);

  const handleSimulateRecovery = async (agentCode = 'AGT-REQ-01') => {
    try {
      setSimulating(true);
      const res = await simulateVisualizerRecovery(agentCode);
      setActiveSequence(res);
      setCurrentStepIndex(0);
      setIsAutoPlaying(true);
      loadRecoveryHistory();
    } catch (err) {
      console.error('Simulation error:', err);
    } finally {
      setSimulating(false);
    }
  };

  // Auto-play steps timer
  useEffect(() => {
    if (!isAutoPlaying || !activeSequence?.steps) return;

    if (currentStepIndex < activeSequence.steps.length - 1) {
      const timer = setTimeout(() => {
        setCurrentStepIndex((prev) => prev + 1);
      }, 1400);
      return () => clearTimeout(timer);
    } else {
      setIsAutoPlaying(false);
    }
  }, [isAutoPlaying, currentStepIndex, activeSequence]);

  const currentStep = activeSequence?.steps?.[currentStepIndex] || null;

  return (
    <div className="space-y-6">
      {/* View Header */}
      <div className="bg-[#0b152e] border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-amber-400 text-xs font-bold uppercase tracking-wider mb-1">
              <ShieldAlert className="w-4 h-4" />
              <span>Fault Tolerance & Supervisor Failover Engine</span>
            </div>
            <h2 className="text-xl font-extrabold text-white tracking-tight">
              Agent Failure Detection & Atomic Task Reassignment
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Live visualization of supervisor watchdog heartbeats, worker failure detection, queue reassignment, and authoritative recovery.
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <button
              disabled={simulating}
              onClick={() => handleSimulateRecovery('AGT-REQ-01')}
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 hover:bg-amber-500/30 transition disabled:opacity-50 shadow-lg shadow-amber-500/10"
            >
              <Zap className="w-4 h-4" />
              <span>{simulating ? 'Simulating Failover...' : 'Trigger Agent Failure & Recovery'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Visual Recovery Canvas */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Topology Node Movement Map */}
        <div className="lg:col-span-2 bg-[#070d1e] rounded-2xl border border-slate-800 p-6 shadow-2xl relative flex flex-col justify-between min-h-[480px]">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-6">
              <span className="text-xs font-bold uppercase text-slate-400 tracking-wider flex items-center space-x-2">
                <Activity className="w-4 h-4 text-amber-400" />
                <span>Failover Sequence Canvas</span>
              </span>
              {activeSequence && (
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono text-cyan-400 font-bold">
                    Step {currentStepIndex + 1} of {activeSequence.steps.length}
                  </span>
                  <button
                    onClick={() => setIsAutoPlaying(!isAutoPlaying)}
                    className="p-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-300 hover:text-white"
                  >
                    {isAutoPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                  </button>
                </div>
              )}
            </div>

            {/* Architecture Node Diagram */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 my-6">
              {/* Failed Agent Node */}
              <div
                className={`p-4 rounded-2xl border transition-all duration-300 ${
                  currentStep?.status === 'FAILED'
                    ? 'bg-red-950/40 border-red-500 shadow-xl shadow-red-500/20 ring-2 ring-red-500/40'
                    : currentStep?.agent_id === 'AGT-REQ-01' && currentStep?.status === 'PROCESSING'
                    ? 'bg-cyan-950/30 border-cyan-500'
                    : 'bg-slate-900/60 border-slate-800'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <Cpu className="w-5 h-5 text-cyan-400" />
                  <span
                    className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                      currentStep?.status === 'FAILED'
                        ? 'bg-red-500/20 text-red-300'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {currentStep?.status === 'FAILED' ? 'CRASHED / UNRESPONSIVE' : 'AGT-REQ-01'}
                  </span>
                </div>
                <h4 className="text-sm font-bold text-white">Request Worker 1</h4>
                <span className="text-[10px] font-mono text-slate-400 block mt-1">Status: {currentStep?.agent_id === 'AGT-REQ-01' ? currentStep.status : 'STANDBY'}</span>
              </div>

              {/* Central Supervisor Watchdog Node */}
              <div
                className={`p-4 rounded-2xl border transition-all duration-300 ${
                  currentStep?.agent_id === 'AGT-SUPERVISOR-01'
                    ? 'bg-amber-950/40 border-amber-500 shadow-xl shadow-amber-500/20 ring-2 ring-amber-500/40'
                    : 'bg-slate-900/60 border-slate-800'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <ShieldCheck className="w-5 h-5 text-emerald-400" />
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400">
                    SUPERVISOR
                  </span>
                </div>
                <h4 className="text-sm font-bold text-white">Supervisor Watchdog</h4>
                <span className="text-[10px] font-mono text-slate-400 block mt-1">Watchdog: 30s Heartbeat Check</span>
              </div>

              {/* Failover Backup Worker Node */}
              <div
                className={`p-4 rounded-2xl border transition-all duration-300 ${
                  currentStep?.agent_id === 'AGT-REQ-02'
                    ? 'bg-emerald-950/40 border-emerald-500 shadow-xl shadow-emerald-500/20 ring-2 ring-emerald-500/40'
                    : 'bg-slate-900/60 border-slate-800'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <Cpu className="w-5 h-5 text-emerald-400" />
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                    AGT-REQ-02
                  </span>
                </div>
                <h4 className="text-sm font-bold text-white">Request Worker 2</h4>
                <span className="text-[10px] font-mono text-slate-400 block mt-1">
                  Status: {currentStep?.agent_id === 'AGT-REQ-02' ? currentStep.status : 'AVAILABLE'}
                </span>
              </div>
            </div>

            {/* Active Stage Callout */}
            {currentStep && (
              <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 backdrop-blur-md space-y-2 animate-fade-in">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-cyan-400 uppercase">
                    Stage {currentStep.step}: {currentStep.stage}
                  </span>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      currentStep.status === 'FAILED'
                        ? 'bg-red-500/20 text-red-300'
                        : currentStep.status === 'COMPLETED' || currentStep.status === 'AUDITED'
                        ? 'bg-emerald-500/20 text-emerald-300'
                        : 'bg-cyan-500/20 text-cyan-300'
                    }`}
                  >
                    {currentStep.status}
                  </span>
                </div>
                <h3 className="text-base font-extrabold text-white">{currentStep.title}</h3>
                <p className="text-xs text-slate-300">{currentStep.detail}</p>
              </div>
            )}
          </div>

          {/* Step Timeline Navigation Bar */}
          {activeSequence && (
            <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
              <div className="flex items-center space-x-1.5 overflow-x-auto">
                {activeSequence.steps.map((st, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setCurrentStepIndex(idx);
                      setIsAutoPlaying(false);
                    }}
                    className={`w-7 h-7 rounded-lg text-xs font-bold font-mono transition ${
                      currentStepIndex === idx
                        ? 'bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/40'
                        : idx < currentStepIndex
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                    }`}
                  >
                    {idx + 1}
                  </button>
                ))}
              </div>

              <span className="text-[11px] text-slate-400 font-mono">
                {activeSequence.failure_id}
              </span>
            </div>
          )}
        </div>

        {/* Side Panel: Chronological Step Inspector */}
        <div className="bg-[#0b152e] rounded-2xl border border-slate-800 p-5 shadow-xl flex flex-col justify-between">
          <div>
            <div className="pb-3 border-b border-slate-800 mb-4">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                <Terminal className="w-4 h-4 text-amber-400" />
                <span>Failover Milestone Log</span>
              </h3>
            </div>

            {activeSequence ? (
              <div className="space-y-3">
                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs space-y-1">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Failed Worker:</span>
                    <span className="font-mono text-red-400 font-bold">{activeSequence.failed_agent}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Target Request:</span>
                    <span className="font-mono text-cyan-400 font-bold">{activeSequence.request_code}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Backup Worker:</span>
                    <span className="font-mono text-emerald-400 font-bold">{activeSequence.backup_worker}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Audit ID:</span>
                    <span className="font-mono text-amber-400">{activeSequence.audit_id}</span>
                  </div>
                </div>

                <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                  {activeSequence.steps.map((st, i) => (
                    <div
                      key={i}
                      onClick={() => setCurrentStepIndex(i)}
                      className={`p-2.5 rounded-xl border text-xs cursor-pointer transition ${
                        currentStepIndex === i
                          ? 'bg-slate-900 border-cyan-500 shadow-md'
                          : 'bg-slate-950/40 border-slate-850 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[10px] font-mono text-cyan-400 font-bold">Step {st.step}</span>
                        <span
                          className={`text-[9px] font-bold px-1.5 py-0.2 rounded ${
                            st.status === 'FAILED'
                              ? 'bg-red-500/20 text-red-400'
                              : st.status === 'COMPLETED'
                              ? 'bg-emerald-500/20 text-emerald-400'
                              : 'bg-slate-800 text-slate-300'
                          }`}
                        >
                          {st.status}
                        </span>
                      </div>
                      <h5 className="font-bold text-white text-[11px] truncate">{st.title}</h5>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-16 text-slate-500 space-y-2">
                <ShieldAlert className="w-12 h-12 mx-auto text-slate-600" />
                <h4 className="text-sm font-bold text-slate-400">Trigger Recovery Simulation</h4>
                <p className="text-xs max-w-xs mx-auto">
                  Click 'Trigger Agent Failure & Recovery' to observe the supervisor detect a crashed agent, isolate its task, and reassign it atomically.
                </p>
              </div>
            )}
          </div>

          <div className="pt-4 border-t border-slate-800 text-[10px] text-slate-500 font-mono">
            Authoritative State: PostgreSQL • Zero Message Loss
          </div>
        </div>
      </div>
    </div>
  );
};
