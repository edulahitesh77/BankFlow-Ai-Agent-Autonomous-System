import React from 'react';
import {
  X,
  Cpu,
  Activity,
  Layers,
  Clock,
  CheckCircle2,
  AlertTriangle,
  RotateCw,
  Heart,
  ShieldCheck,
  Send,
  Inbox,
  Hash,
} from 'lucide-react';

export const AgentInspectorDrawer = ({ agent, onClose, onSelectRequest }) => {
  if (!agent) return null;

  const {
    id,
    agent_code,
    agent_name,
    agent_type,
    category,
    status = 'IDLE',
    current_request_id,
    current_stage,
    completed_tasks = 0,
    failed_tasks = 0,
    last_heartbeat,
    last_active_at,
    supported_skills = [],
    health_status,
  } = agent;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-[#091126]/98 backdrop-blur-xl border-l border-slate-800 shadow-2xl flex flex-col transform transition-transform duration-300">
      {/* Top Header */}
      <div className="p-4 sm:p-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide">{agent_name || agent_code}</h3>
            <div className="flex items-center space-x-2 text-xs text-slate-400 font-mono">
              <span className="text-emerald-400 font-bold">{id ? `#${id}` : 'MESA'}</span>
              <span>•</span>
              <span>{agent_type}</span>
            </div>
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
        {/* Current State Card */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs uppercase font-semibold text-slate-400">Operational State</span>
            <span
              className={`px-2.5 py-0.5 rounded-full text-xs font-bold font-mono border ${
                status === 'PROCESSING'
                  ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                  : status === 'FAILED'
                  ? 'bg-red-500/20 text-red-300 border-red-500/40'
                  : status === 'RECOVERING'
                  ? 'bg-purple-500/20 text-purple-300 border-purple-500/40'
                  : 'bg-slate-800 text-slate-300 border-slate-700'
              }`}
            >
              {status}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs pt-1">
            <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-850">
              <span className="text-[10px] text-slate-400 block font-semibold uppercase">Category</span>
              <span className="text-white font-medium">{category || 'CORE_PIPELINE'}</span>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-850">
              <span className="text-[10px] text-slate-400 block font-semibold uppercase">Health</span>
              <span className="text-emerald-400 font-medium">{health_status || 'HEALTHY'}</span>
            </div>
          </div>
        </div>

        {/* Current Request Card */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2.5">
          <span className="text-xs uppercase font-semibold text-slate-400 block">Active Task Binding</span>
          {current_request_id ? (
            <div className="flex items-center justify-between p-3 rounded-xl bg-cyan-950/50 border border-cyan-800/50">
              <div>
                <span className="text-[10px] text-cyan-400 font-semibold uppercase block">Request ID</span>
                <span className="font-mono text-sm font-bold text-white">{current_request_id}</span>
              </div>
              {onSelectRequest && (
                <button
                  onClick={() => onSelectRequest(current_request_id)}
                  className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition"
                >
                  Inspect Journey
                </button>
              )}
            </div>
          ) : (
            <div className="p-3 rounded-xl bg-slate-950/40 border border-slate-850 text-center text-xs text-slate-400 italic">
              Currently idle on standby. Ready to accept incoming tasks.
            </div>
          )}
          <div className="text-[11px] text-slate-400 flex items-center justify-between pt-1">
            <span>Execution Stage:</span>
            <span className="font-mono text-slate-200">{current_stage || status}</span>
          </div>
        </div>

        {/* Workload & Telemetry Counters */}
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
            <span className="text-[10px] uppercase font-semibold text-slate-400 block">Completed</span>
            <span className="text-lg font-bold font-mono text-emerald-400 mt-0.5 block">{completed_tasks}</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
            <span className="text-[10px] uppercase font-semibold text-slate-400 block">Failed</span>
            <span className="text-lg font-bold font-mono text-red-400 mt-0.5 block">{failed_tasks}</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
            <span className="text-[10px] uppercase font-semibold text-slate-400 block">Success %</span>
            <span className="text-lg font-bold font-mono text-cyan-400 mt-0.5 block">
              {completed_tasks + failed_tasks > 0
                ? Math.round((completed_tasks / (completed_tasks + failed_tasks)) * 100)
                : 100}
              %
            </span>
          </div>
        </div>

        {/* Heartbeat & Timestamps */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2 text-xs">
          <div className="flex items-center justify-between text-slate-400">
            <span className="flex items-center space-x-1.5">
              <Heart className="w-3.5 h-3.5 text-rose-400" />
              <span>Last Heartbeat:</span>
            </span>
            <span className="font-mono text-slate-200">
              {last_heartbeat ? new Date(last_heartbeat).toLocaleTimeString() : 'Recent'}
            </span>
          </div>
          <div className="flex items-center justify-between text-slate-400">
            <span className="flex items-center space-x-1.5">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              <span>Last Active:</span>
            </span>
            <span className="font-mono text-slate-200">
              {last_active_at ? new Date(last_active_at).toLocaleTimeString() : 'Active'}
            </span>
          </div>
        </div>

        {/* Supported Capabilities */}
        {supported_skills && supported_skills.length > 0 && (
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
            <span className="text-xs uppercase font-semibold text-slate-400 block">Assigned Skills</span>
            <div className="flex flex-wrap gap-1.5">
              {supported_skills.map((skill, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-emerald-400 border border-slate-700"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Drawer Footer */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/80 flex justify-end">
        <button
          onClick={onClose}
          className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition"
        >
          Close Inspector
        </button>
      </div>
    </div>
  );
};
