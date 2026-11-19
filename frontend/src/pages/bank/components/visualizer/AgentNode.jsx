import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import {
  User,
  Inbox,
  Cpu,
  ShieldCheck,
  Briefcase,
  AlertTriangle,
  RotateCw,
  CheckCircle2,
  Activity,
  Layers,
  Clock,
} from 'lucide-react';

const getStatusStyles = (status) => {
  switch (status) {
    case 'PROCESSING':
      return {
        badgeBg: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40',
        cardBorder: 'border-cyan-500/80 shadow-[0_0_20px_rgba(6,182,212,0.35)]',
        accent: 'text-cyan-400',
        ring: 'ring-2 ring-cyan-500/50',
      };
    case 'VERIFYING':
      return {
        badgeBg: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40',
        cardBorder: 'border-indigo-500/80 shadow-[0_0_20px_rgba(99,102,241,0.35)]',
        accent: 'text-indigo-400',
        ring: 'ring-2 ring-indigo-500/50',
      };
    case 'BUSY':
      return {
        badgeBg: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
        cardBorder: 'border-amber-500/80 shadow-[0_0_15px_rgba(245,158,11,0.25)]',
        accent: 'text-amber-400',
        ring: 'ring-1 ring-amber-500/40',
      };
    case 'FAILED':
      return {
        badgeBg: 'bg-red-500/20 text-red-300 border-red-500/40',
        cardBorder: 'border-red-500 shadow-[0_0_25px_rgba(239,68,68,0.4)] animate-pulse',
        accent: 'text-red-400',
        ring: 'ring-2 ring-red-500/60',
      };
    case 'UNRESPONSIVE':
      return {
        badgeBg: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
        cardBorder: 'border-rose-600 shadow-[0_0_20px_rgba(225,29,72,0.3)]',
        accent: 'text-rose-400',
        ring: 'ring-1 ring-rose-500/50',
      };
    case 'RECOVERING':
      return {
        badgeBg: 'bg-purple-500/20 text-purple-300 border-purple-500/40',
        cardBorder: 'border-purple-500 shadow-[0_0_20px_rgba(168,85,247,0.35)]',
        accent: 'text-purple-400',
        ring: 'ring-2 ring-purple-500/50',
      };
    case 'COMPLETED':
      return {
        badgeBg: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
        cardBorder: 'border-emerald-500/60 shadow-[0_0_15px_rgba(16,185,129,0.2)]',
        accent: 'text-emerald-400',
        ring: '',
      };
    case 'IDLE':
    default:
      return {
        badgeBg: 'bg-slate-800/80 text-slate-400 border-slate-700',
        cardBorder: 'border-slate-800 hover:border-slate-700 shadow-md',
        accent: 'text-slate-400',
        ring: '',
      };
  }
};

const getAgentIcon = (agentType) => {
  switch (agentType) {
    case 'CUSTOMER':
      return User;
    case 'INTAKE':
      return Inbox;
    case 'REQUEST':
      return Cpu;
    case 'VERIFICATION':
      return ShieldCheck;
    case 'SERVICE':
      return Briefcase;
    default:
      return Activity;
  }
};

export const AgentNode = memo(({ data, selected }) => {
  const {
    id,
    agent_code,
    agent_name,
    agent_type,
    status = 'IDLE',
    current_request_id,
    current_stage,
    completed_tasks = 0,
    failed_tasks = 0,
    health_status,
  } = data;

  const styles = getStatusStyles(status);
  const Icon = getAgentIcon(agent_type);
  const isSelected = selected;

  return (
    <div
      className={`relative min-w-[220px] max-w-[260px] rounded-2xl bg-[#091124]/95 backdrop-blur-md p-3.5 border transition-all duration-300 cursor-pointer ${
        styles.cardBorder
      } ${styles.ring} ${isSelected ? 'ring-2 ring-emerald-400 scale-[1.02]' : ''}`}
    >
      {/* Target Handle (Left) */}
      <Handle
        type="target"
        position={Position.Left}
        className="w-2.5 h-2.5 bg-slate-400 border-2 border-[#070d1e] !-left-1.5"
      />

      {/* Target Handle (Top for Supervisor links) */}
      <Handle
        type="target"
        position={Position.Top}
        id="top"
        className="w-2 h-2 bg-indigo-400 border-2 border-[#070d1e] !-top-1"
      />

      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-2.5">
        <div className="flex items-center space-x-2 min-w-0">
          <div
            className={`w-8 h-8 rounded-xl flex items-center justify-center border ${styles.badgeBg} ${styles.accent}`}
          >
            <Icon className="w-4 h-4" />
          </div>
          <div className="min-w-0 flex-1">
            <h4 className="text-xs font-bold text-white truncate leading-tight">{agent_name || agent_code}</h4>
            <div className="flex items-center space-x-1.5 text-[10px] text-slate-400 font-mono">
              <span className="text-emerald-400 font-bold">{id ? `#${id}` : 'SIM'}</span>
              <span>•</span>
              <span className="truncate">{agent_code}</span>
            </div>
          </div>
        </div>

        {/* Status Pill */}
        <span
          className={`px-2 py-0.5 rounded-full text-[10px] font-bold border uppercase tracking-wider flex-shrink-0 flex items-center space-x-1 ${styles.badgeBg}`}
        >
          {status === 'PROCESSING' && <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping mr-0.5" />}
          {status === 'FAILED' && <AlertTriangle className="w-2.5 h-2.5 mr-0.5 text-red-400" />}
          {status === 'RECOVERING' && <RotateCw className="w-2.5 h-2.5 mr-0.5 animate-spin text-purple-400" />}
          <span>{status}</span>
        </span>
      </div>

      {/* Assigned Request Slot */}
      <div className="mb-2.5 px-2.5 py-1.5 rounded-xl bg-slate-900/80 border border-slate-800 text-[11px] flex items-center justify-between">
        <span className="text-slate-400 text-[10px] uppercase font-semibold">Assigned Req:</span>
        {current_request_id ? (
          <span className="font-mono text-cyan-300 font-bold bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/50">
            {current_request_id}
          </span>
        ) : (
          <span className="text-slate-400 text-[10px] italic">Standby</span>
        )}
      </div>

      {/* Stage & Workload Footer */}
      <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1.5 border-t border-slate-800/80">
        <div className="flex items-center space-x-1 truncate max-w-[120px]">
          <Layers className="w-3 h-3 text-slate-400 flex-shrink-0" />
          <span className="truncate">{current_stage || status}</span>
        </div>
        <div className="flex items-center space-x-1.5 font-mono text-slate-300">
          <span className="text-emerald-400 font-semibold">{completed_tasks} done</span>
          {failed_tasks > 0 && <span className="text-red-400">({failed_tasks} fail)</span>}
        </div>
      </div>

      {/* Source Handle (Right) */}
      <Handle
        type="source"
        position={Position.Right}
        className="w-2.5 h-2.5 bg-emerald-400 border-2 border-[#070d1e] !-right-1.5"
      />
    </div>
  );
});
