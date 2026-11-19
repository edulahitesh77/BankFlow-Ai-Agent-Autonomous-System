import React, { useState, useEffect } from 'react';
import {
  X,
  BarChart2,
  TrendingUp,
  Activity,
  Cpu,
  Clock,
  CheckCircle2,
  AlertTriangle,
  RotateCw,
  Layers,
  Zap,
} from 'lucide-react';
import { fetchVisualizerAnalytics } from '../../../../api/auth';

export const PerformanceAnalyticsDrawer = ({ isOpen, onClose }) => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchVisualizerAnalytics();
      setAnalytics(data);
    } catch (err) {
      setError(err.message || 'Failed to load performance analytics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadAnalytics();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const overview = analytics?.overview || {};
  const statusDist = analytics?.status_distribution || {};
  const agentUtils = analytics?.agent_utilization || [];
  const eventVols = analytics?.event_volume || [];

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-xl bg-[#091126]/98 backdrop-blur-xl border-l border-slate-800 shadow-2xl flex flex-col transform transition-transform duration-300">
      {/* Header */}
      <div className="p-4 sm:p-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
            <BarChart2 className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide">Performance & Fleet Analytics</h3>
            <span className="text-xs text-slate-400 font-mono">Live Multi-Agent Telemetry & Throughput</span>
          </div>
        </div>

        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Content Scroll */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-5">
        {loading ? (
          <div className="py-24 text-center space-y-3">
            <div className="w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p className="text-xs text-slate-400 font-medium">Calculating workload and utilization metrics...</p>
          </div>
        ) : error ? (
          <div className="p-4 rounded-xl bg-red-950/60 border border-red-800 text-xs text-red-200">
            {error}
          </div>
        ) : (
          <>
            {/* KPI Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-[10px] uppercase font-semibold text-slate-400 block">Avg Duration</span>
                <span className="text-lg font-bold font-mono text-cyan-400 mt-0.5 block">
                  {overview.avg_processing_time_sec}s
                </span>
                <span className="text-[9px] text-slate-500">Processing latency</span>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-[10px] uppercase font-semibold text-slate-400 block">Avg Wait</span>
                <span className="text-lg font-bold font-mono text-indigo-400 mt-0.5 block">
                  {overview.avg_waiting_time_sec}s
                </span>
                <span className="text-[9px] text-slate-500">Queue latency</span>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-[10px] uppercase font-semibold text-slate-400 block">Throughput</span>
                <span className="text-lg font-bold font-mono text-emerald-400 mt-0.5 block">
                  {overview.concurrent_throughput_rpm}
                </span>
                <span className="text-[9px] text-slate-500">Reqs / min capacity</span>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-[10px] uppercase font-semibold text-slate-400 block">Recovery Time</span>
                <span className="text-lg font-bold font-mono text-purple-400 mt-0.5 block">
                  {overview.avg_recovery_time_sec}s
                </span>
                <span className="text-[9px] text-slate-500">{overview.recovery_rate_pct}% success</span>
              </div>
            </div>

            {/* Fleet Status Counts */}
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
              <span className="text-xs uppercase font-semibold text-slate-400 block">Fleet Headcount</span>
              <div className="grid grid-cols-4 gap-2 text-center text-xs">
                <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-850">
                  <span className="text-[9px] uppercase font-semibold text-slate-400 block">Total</span>
                  <span className="text-base font-bold font-mono text-white mt-0.5 block">
                    {overview.total_agents}
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-cyan-950/40 border border-cyan-800/40">
                  <span className="text-[9px] uppercase font-semibold text-cyan-400 block">Busy / Active</span>
                  <span className="text-base font-bold font-mono text-cyan-300 mt-0.5 block">
                    {overview.active_workers}
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-850">
                  <span className="text-[9px] uppercase font-semibold text-slate-400 block">Idle Standby</span>
                  <span className="text-base font-bold font-mono text-slate-300 mt-0.5 block">
                    {overview.idle_agents}
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-red-950/40 border border-red-800/40">
                  <span className="text-[9px] uppercase font-semibold text-red-400 block">Failed</span>
                  <span className="text-base font-bold font-mono text-red-300 mt-0.5 block">
                    {overview.failed_agents}
                  </span>
                </div>
              </div>
            </div>

            {/* Agent Utilization Progress Bars */}
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs uppercase font-semibold text-slate-400">Agent Workload & Utilization</span>
                <span className="text-[10px] text-slate-500 font-mono">Completed vs Target</span>
              </div>

              <div className="space-y-2.5">
                {agentUtils.slice(0, 8).map((u, i) => (
                  <div key={i} className="space-y-1">
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="text-slate-300 font-medium truncate max-w-[200px]">
                        {u.agent_code}
                      </span>
                      <div className="flex items-center space-x-2">
                        <span className="text-slate-400 text-[11px]">{u.completed} reqs</span>
                        <span className="text-emerald-400 font-bold">{u.utilization_pct}%</span>
                      </div>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-emerald-500 to-cyan-400 rounded-full transition-all duration-500"
                        style={{ width: `${Math.min(100, Math.max(5, u.utilization_pct))}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Request Status Distribution Bars */}
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
              <span className="text-xs uppercase font-semibold text-slate-400 block">
                Request Status Distribution
              </span>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
                {Object.entries(statusDist).map(([stKey, stVal]) => (
                  <div key={stKey} className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-850">
                    <span className="text-[9px] uppercase font-semibold text-slate-400 block truncate">
                      {stKey}
                    </span>
                    <span className="text-sm font-bold font-mono text-white mt-0.5 block">{stVal}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Message Communication Volume */}
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
              <span className="text-xs uppercase font-semibold text-slate-400 block">
                Message Volume by Event Type
              </span>
              <div className="space-y-2">
                {eventVols.slice(0, 6).map((ev, i) => (
                  <div key={i} className="flex items-center justify-between text-xs p-2 rounded-lg bg-slate-950/40">
                    <span className="font-mono text-slate-300 text-[11px] truncate max-w-[260px]">
                      {ev.event_type}
                    </span>
                    <span className="font-mono text-cyan-400 font-bold bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                      {ev.count} msgs
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/80 flex items-center justify-between">
        <button
          onClick={loadAnalytics}
          className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
        >
          Refresh Telemetry
        </button>
        <button
          onClick={onClose}
          className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition"
        >
          Close Analytics
        </button>
      </div>
    </div>
  );
};
