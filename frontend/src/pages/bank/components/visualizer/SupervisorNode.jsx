import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { ShieldCheck, Activity, Heart, AlertOctagon, RotateCw, Eye } from 'lucide-react';

export const SupervisorNode = memo(({ data, selected }) => {
  const {
    id,
    agent_code = 'AGT-SUPERVISOR-01',
    agent_name = 'Supervisor Agent',
    status = 'IDLE',
    monitored_count = 8,
    unresponsive_count = 0,
    recovery_count = 0,
    health_status = 'HEALTHY',
    last_heartbeat,
  } = data;

  const isFailed = status === 'FAILED' || unresponsive_count > 0;
  const isRecovering = status === 'RECOVERING' || recovery_count > 0;

  return (
    <div
      className={`relative min-w-[280px] max-w-[320px] rounded-2xl bg-gradient-to-b from-[#111c38]/95 to-[#0b1329]/95 backdrop-blur-md p-4 border transition-all duration-300 cursor-pointer shadow-xl ${
        isFailed
          ? 'border-red-500 shadow-[0_0_25px_rgba(239,68,68,0.4)]'
          : isRecovering
          ? 'border-purple-500 shadow-[0_0_20px_rgba(168,85,247,0.3)]'
          : 'border-emerald-500/60 hover:border-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.2)]'
      } ${selected ? 'ring-2 ring-emerald-400 scale-[1.02]' : ''}`}
    >
      {/* Target Handle */}
      <Handle
        type="target"
        position={Position.Left}
        className="w-2.5 h-2.5 bg-emerald-400 border-2 border-[#070d1e] !-left-1.5"
      />

      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex items-center space-x-2.5">
          <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shadow-inner">
            <Eye className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-1.5">
              <h4 className="text-xs font-bold text-white tracking-wide">{agent_name}</h4>
              <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                OVERSEER
              </span>
            </div>
            <div className="text-[10px] text-slate-400 font-mono">
              <span className="text-emerald-400 font-bold">{id ? `#${id}` : 'ROOT'}</span> • {agent_code}
            </div>
          </div>
        </div>

        {/* Supervision Live Radar */}
        <div className="flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-700/60">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
          <span>ACTIVE</span>
        </div>
      </div>

      {/* Heartbeat & Metrics Grid */}
      <div className="grid grid-cols-3 gap-2 mb-2.5">
        <div className="p-2 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
          <div className="text-[9px] uppercase text-slate-400 font-semibold">Fleet</div>
          <div className="text-xs font-bold text-white font-mono mt-0.5">{monitored_count} Agents</div>
        </div>
        <div className="p-2 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
          <div className="text-[9px] uppercase text-slate-400 font-semibold">Unresponsive</div>
          <div
            className={`text-xs font-bold font-mono mt-0.5 ${
              unresponsive_count > 0 ? 'text-red-400' : 'text-slate-300'
            }`}
          >
            {unresponsive_count}
          </div>
        </div>
        <div className="p-2 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
          <div className="text-[9px] uppercase text-slate-400 font-semibold">Recoveries</div>
          <div className="text-xs font-bold text-purple-400 font-mono mt-0.5">{recovery_count}</div>
        </div>
      </div>

      {/* Heartbeat Status */}
      <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1.5 border-t border-slate-800/80">
        <div className="flex items-center space-x-1.5">
          <Heart className="w-3 h-3 text-rose-400 animate-pulse" />
          <span>Periodic Heartbeats:</span>
          <span className="text-emerald-400 font-mono font-medium">HEALTHY</span>
        </div>
        <span className="text-[9px] text-slate-400 font-mono">Failover: AUTO</span>
      </div>

      {/* Source Handles (Bottom for dispatching supervisory signals to all pipeline agents) */}
      <Handle
        type="source"
        position={Position.Bottom}
        id="supervisor-out"
        className="w-2.5 h-2.5 bg-indigo-400 border-2 border-[#070d1e] !-bottom-1.5"
      />
    </div>
  );
});
