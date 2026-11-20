import React, { useState } from 'react';
import {
  User,
  Inbox,
  Cpu,
  ShieldCheck,
  Briefcase,
  Eye,
  AlertTriangle,
  RotateCw,
  CheckCircle2,
  Activity,
  Layers,
  Clock,
  ExternalLink,
  Flame,
  Radio,
  Search,
  Filter,
} from 'lucide-react';

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
    case 'SUPERVISOR':
      return Eye;
    default:
      return Activity;
  }
};

const getStatusBadge = (status) => {
  switch (status) {
    case 'PROCESSING':
      return {
        bg: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/50 shadow-sm shadow-cyan-500/20',
        dot: 'bg-cyan-400 animate-ping',
        text: 'PROCESSING',
      };
    case 'VERIFYING':
      return {
        bg: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/50 shadow-sm shadow-indigo-500/20',
        dot: 'bg-indigo-400 animate-ping',
        text: 'VERIFYING',
      };
    case 'BUSY':
      return {
        bg: 'bg-amber-500/20 text-amber-300 border-amber-500/50',
        dot: 'bg-amber-400',
        text: 'BUSY',
      };
    case 'FAILED':
      return {
        bg: 'bg-red-500/25 text-red-300 border-red-500/60 shadow-md shadow-red-500/30',
        dot: 'bg-red-400 animate-pulse',
        text: 'FAILED',
      };
    case 'UNRESPONSIVE':
      return {
        bg: 'bg-rose-500/25 text-rose-300 border-rose-500/60',
        dot: 'bg-rose-400',
        text: 'UNRESPONSIVE',
      };
    case 'RECOVERING':
      return {
        bg: 'bg-purple-500/25 text-purple-300 border-purple-500/60',
        dot: 'bg-purple-400 animate-spin',
        text: 'RECOVERING',
      };
    case 'COMPLETED':
      return {
        bg: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50',
        dot: 'bg-emerald-400',
        text: 'COMPLETED',
      };
    case 'IDLE':
    default:
      return {
        bg: 'bg-slate-800 text-slate-400 border-slate-700',
        dot: 'bg-emerald-500',
        text: 'IDLE / STANDBY',
      };
  }
};

const getPipelineStageStep = (stage) => {
  if (!stage || stage === 'IDLE') return 0;
  const s = String(stage).toUpperCase();
  if (s.includes('NEW') || s.includes('CUSTOMER')) return 1;
  if (s.includes('INTAKE') || s.includes('CLASSIF')) return 2;
  if (s.includes('REQUEST') || s.includes('PROCESSING') || s.includes('ASSIGN')) return 3;
  if (s.includes('VERIF') || s.includes('KYC') || s.includes('COMPLIANCE')) return 4;
  if (s.includes('SERVICE') || s.includes('SETTLE') || s.includes('COMPLETE')) return 5;
  return 3;
};

export const AgentWorkDeck = ({
  agents = [],
  metrics = {},
  onFocusAgentOnGraph,
  onSelectRequest,
}) => {
  const [filterCategory, setFilterCategory] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Normalize list of agents
  const displayAgents = agents && agents.length > 0 ? agents : [];

  const filteredAgents = displayAgents.filter((agent) => {
    const matchesCategory =
      filterCategory === 'ALL' ||
      (filterCategory === 'CORE' && (agent.agent_type === 'CUSTOMER' || agent.agent_type === 'INTAKE' || agent.agent_type === 'VERIFICATION')) ||
      (filterCategory === 'REQUEST' && agent.agent_type === 'REQUEST') ||
      (filterCategory === 'SERVICE' && agent.agent_type === 'SERVICE') ||
      (filterCategory === 'SUPERVISOR' && agent.agent_type === 'SUPERVISOR');

    const matchesSearch =
      searchQuery.trim() === '' ||
      (agent.agent_name && agent.agent_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (agent.agent_code && agent.agent_code.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (agent.current_request_id && agent.current_request_id.toLowerCase().includes(searchQuery.toLowerCase()));

    return matchesCategory && matchesSearch;
  });

  const activeWorkingCount = displayAgents.filter(
    (a) => a.current_request_id || a.status === 'PROCESSING' || a.status === 'VERIFYING' || a.status === 'BUSY'
  ).length;

  return (
    <div className="space-y-6">
      {/* Overview Status Ribbon */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3.5 rounded-2xl bg-[#091124] border border-slate-800 shadow-lg">
          <div className="flex items-center space-x-2 text-slate-400 text-xs font-semibold uppercase">
            <Radio className="w-4 h-4 text-cyan-400" />
            <span>Monitored Swarm</span>
          </div>
          <div className="text-xl font-bold font-mono text-white mt-1">
            {displayAgents.length} <span className="text-xs text-slate-400 font-normal">Active Agents</span>
          </div>
        </div>

        <div className="p-3.5 rounded-2xl bg-[#091124] border border-cyan-900/50 shadow-lg">
          <div className="flex items-center space-x-2 text-cyan-400 text-xs font-semibold uppercase">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
            <span>Currently Working</span>
          </div>
          <div className="text-xl font-bold font-mono text-cyan-300 mt-1">
            {activeWorkingCount} <span className="text-xs text-slate-400 font-normal">Assigned</span>
          </div>
        </div>

        <div className="p-3.5 rounded-2xl bg-[#091124] border border-slate-800 shadow-lg">
          <div className="flex items-center space-x-2 text-emerald-400 text-xs font-semibold uppercase">
            <CheckCircle2 className="w-4 h-4" />
            <span>Processed</span>
          </div>
          <div className="text-xl font-bold font-mono text-emerald-300 mt-1">
            {metrics.processed_requests || 0}{' '}
            <span className="text-xs text-slate-400 font-normal">Workflows</span>
          </div>
        </div>

        <div className="p-3.5 rounded-2xl bg-[#091124] border border-slate-800 shadow-lg">
          <div className="flex items-center space-x-2 text-indigo-400 text-xs font-semibold uppercase">
            <Layers className="w-4 h-4" />
            <span>In-Flight Queue</span>
          </div>
          <div className="text-xl font-bold font-mono text-indigo-300 mt-1">
            {metrics.pending_requests || 0}{' '}
            <span className="text-xs text-slate-400 font-normal">Pending</span>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-[#091124] border border-slate-800 rounded-2xl p-3 shadow-xl flex flex-wrap items-center justify-between gap-3">
        {/* Category Pills */}
        <div className="flex items-center space-x-1.5 overflow-x-auto w-full sm:w-auto">
          {[
            { id: 'ALL', label: `All Agents (${displayAgents.length})` },
            { id: 'CORE', label: 'Core Pipeline' },
            { id: 'REQUEST', label: 'Request Workers' },
            { id: 'SERVICE', label: 'Service Pool' },
            { id: 'SUPERVISOR', label: 'Supervisor' },
          ].map((cat) => (
            <button
              key={cat.id}
              onClick={() => setFilterCategory(cat.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition whitespace-nowrap ${
                filterCategory === cat.id
                  ? 'bg-emerald-500 text-slate-950 shadow-md font-extrabold'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/80'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search agent code or task..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>
      </div>

      {/* Neat Workstation Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
        {filteredAgents.map((agent) => {
          const Icon = getAgentIcon(agent.agent_type);
          const badge = getStatusBadge(agent.status);
          const isWorking = Boolean(agent.current_request_id) || agent.status === 'PROCESSING' || agent.status === 'VERIFYING';
          const stageStep = getPipelineStageStep(agent.current_stage || agent.status);

          return (
            <div
              key={agent.agent_code || agent.id}
              className={`rounded-2xl bg-[#091124] border transition-all duration-300 shadow-xl flex flex-col justify-between overflow-hidden ${
                isWorking
                  ? 'border-cyan-500/70 shadow-[0_0_25px_rgba(6,182,212,0.2)]'
                  : 'border-slate-800 hover:border-slate-700'
              }`}
            >
              {/* Card Header */}
              <div className="p-4 sm:p-5 border-b border-slate-800/80 bg-slate-900/40">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center space-x-3 min-w-0">
                    <div
                      className={`w-11 h-11 rounded-2xl flex items-center justify-center border shadow-inner ${
                        isWorking
                          ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                          : 'bg-slate-800/80 text-slate-300 border-slate-700'
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <h3 className="text-sm font-bold text-white truncate tracking-tight">
                        {agent.agent_name || agent.agent_code}
                      </h3>
                      <div className="flex items-center space-x-2 text-xs text-slate-400 font-mono mt-0.5">
                        <span className="text-emerald-400 font-bold">{agent.id ? `#${agent.id}` : 'MESA'}</span>
                        <span>•</span>
                        <span className="truncate">{agent.agent_code}</span>
                      </div>
                    </div>
                  </div>

                  {/* Status Badge */}
                  <span
                    className={`px-2.5 py-1 rounded-full text-[10px] font-bold border uppercase tracking-wider flex items-center space-x-1.5 ${badge.bg}`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${badge.dot}`}></span>
                    <span>{badge.text}</span>
                  </span>
                </div>
              </div>

              {/* Workstation Core: Current Work Assignment */}
              <div className="p-4 sm:p-5 space-y-4 flex-1">
                <div className="space-y-1.5">
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block">
                    Current Work Assignment
                  </span>

                  {isWorking ? (
                    <div className="p-3.5 rounded-xl bg-cyan-950/60 border border-cyan-500/40 space-y-2.5 shadow-inner">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-cyan-300 flex items-center space-x-1.5">
                          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
                          <span>TASK IN FLIGHT</span>
                        </span>
                        <span className="font-mono text-xs font-black text-white px-2 py-0.5 rounded bg-cyan-900/80 border border-cyan-400/30">
                          {agent.current_request_id || 'PROCESSING'}
                        </span>
                      </div>

                      <div className="flex items-center justify-between text-xs text-slate-300">
                        <span className="text-slate-400">Execution Stage:</span>
                        <span className="font-mono font-bold text-cyan-200">
                          {agent.current_stage || agent.status}
                        </span>
                      </div>

                      {/* 5-Step Pipeline Progress Indicator */}
                      <div className="space-y-1 pt-1">
                        <div className="flex justify-between text-[9px] font-mono text-slate-400 uppercase">
                          <span>Submit</span>
                          <span>Intake</span>
                          <span>Worker</span>
                          <span>Verify</span>
                          <span>Settle</span>
                        </div>
                        <div className="grid grid-cols-5 gap-1">
                          {[1, 2, 3, 4, 5].map((step) => (
                            <div
                              key={step}
                              className={`h-1.5 rounded-full transition-all duration-300 ${
                                step < stageStep
                                  ? 'bg-emerald-400'
                                  : step === stageStep
                                  ? 'bg-cyan-400 animate-pulse ring-1 ring-cyan-300'
                                  : 'bg-slate-800'
                              }`}
                            />
                          ))}
                        </div>
                      </div>

                      {agent.current_request_id && onSelectRequest && (
                        <button
                          onClick={() => onSelectRequest(agent.current_request_id)}
                          className="w-full mt-1 py-1.5 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 text-xs font-semibold flex items-center justify-center space-x-1.5 transition"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                          <span>Inspect Request Journey</span>
                        </button>
                      )}
                    </div>
                  ) : (
                    <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-center space-y-1">
                      <span className="text-xs text-slate-300 font-semibold block">
                        Standby • Ready for Next Assignment
                      </span>
                      <span className="text-[11px] text-slate-400 font-mono block">
                        Listening on queue: <span className="text-slate-300 font-bold">bankflow.queue.{agent.agent_code}</span>
                      </span>
                    </div>
                  )}
                </div>

                {/* Performance Metrics Strip */}
                <div className="grid grid-cols-3 gap-2 text-center pt-1">
                  <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80">
                    <span className="text-[10px] uppercase font-semibold text-slate-400 block">Completed</span>
                    <span className="text-sm font-bold font-mono text-emerald-400 mt-0.5 block">
                      {agent.completed_tasks || 0}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80">
                    <span className="text-[10px] uppercase font-semibold text-slate-400 block">Failed</span>
                    <span className="text-sm font-bold font-mono text-red-400 mt-0.5 block">
                      {agent.failed_tasks || 0}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80">
                    <span className="text-[10px] uppercase font-semibold text-slate-400 block">Health</span>
                    <span className="text-xs font-bold font-mono text-emerald-400 mt-1 block">
                      {agent.health_status || 'HEALTHY'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Card Footer: Quick Focus on Graph */}
              <div className="p-3 sm:p-4 border-t border-slate-800/80 bg-slate-900/60 flex items-center justify-between">
                <span className="text-[11px] text-slate-400 font-mono flex items-center space-x-1">
                  <Clock className="w-3.5 h-3.5 text-slate-400" />
                  <span>
                    {agent.last_heartbeat
                      ? new Date(agent.last_heartbeat).toLocaleTimeString()
                      : 'Live Beat Active'}
                  </span>
                </span>

                {onFocusAgentOnGraph && (
                  <button
                    onClick={() => onFocusAgentOnGraph(agent)}
                    className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-xl text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition shadow-sm"
                  >
                    <Eye className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Focus on Graph</span>
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
