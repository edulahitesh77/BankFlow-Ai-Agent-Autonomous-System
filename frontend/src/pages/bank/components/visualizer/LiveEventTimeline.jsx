import React, { useState } from 'react';
import {
  Play,
  Pause,
  Search,
  Filter,
  Clock,
  Radio,
  CheckCircle2,
  AlertTriangle,
  RotateCw,
  Hash,
  Layers,
} from 'lucide-react';

export const LiveEventTimeline = ({
  events = [],
  isStreamPaused = false,
  onTogglePause,
  onSelectRequest,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [agentFilter, setAgentFilter] = useState('ALL');
  const [eventFilter, setEventFilter] = useState('ALL');

  // Extract unique agents and event types for filter dropdowns
  const uniqueAgents = Array.from(new Set(events.map((e) => e.agent_id).filter(Boolean)));
  const uniqueEventTypes = Array.from(new Set(events.map((e) => e.event_type).filter(Boolean)));

  const filteredEvents = events.filter((ev) => {
    const matchesSearch =
      !searchTerm ||
      ev.request_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ev.agent_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ev.reason_code?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesAgent = agentFilter === 'ALL' || ev.agent_id === agentFilter;
    const matchesType = eventFilter === 'ALL' || ev.event_type === eventFilter;
    return matchesSearch && matchesAgent && matchesType;
  });

  return (
    <div className="bg-[#091124] border border-slate-800 rounded-2xl overflow-hidden shadow-xl flex flex-col">
      {/* Timeline Controls Header */}
      <div className="p-3 sm:p-4 border-b border-slate-800 bg-slate-900/60 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Radio className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">Live Event Timeline</h3>
              {isStreamPaused ? (
                <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 font-mono">
                  STREAM PAUSED
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-mono flex items-center space-x-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping mr-1"></span>
                  STREAMING
                </span>
              )}
            </div>
            <span className="text-[10px] text-slate-400 font-mono">
              Chronological agent communications, dispatch decisions, and fault recovery events
            </span>
          </div>
        </div>

        {/* Action Controls & Filters */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Pause / Resume Button */}
          <button
            onClick={onTogglePause}
            className={`inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition ${
              isStreamPaused
                ? 'bg-emerald-500 text-slate-950 hover:bg-emerald-400 shadow-md shadow-emerald-500/20'
                : 'bg-amber-500/10 text-amber-300 hover:bg-amber-500/20 border border-amber-500/30'
            }`}
          >
            {isStreamPaused ? (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Resume Feed</span>
              </>
            ) : (
              <>
                <Pause className="w-3.5 h-3.5 fill-current" />
                <span>Pause Feed</span>
              </>
            )}
          </button>

          {/* Search by Request ID */}
          <div className="relative min-w-[150px] max-w-[200px]">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-500" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search request..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-8 pr-2.5 py-1 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>

          {/* Filter by Agent */}
          <select
            value={agentFilter}
            onChange={(e) => setAgentFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 max-w-[150px]"
          >
            <option value="ALL">All Agents</option>
            {uniqueAgents.map((ag) => (
              <option key={ag} value={ag}>
                {ag}
              </option>
            ))}
          </select>

          {/* Filter by Event Type */}
          <select
            value={eventFilter}
            onChange={(e) => setEventFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 max-w-[160px]"
          >
            <option value="ALL">All Event Types</option>
            {uniqueEventTypes.map((et) => (
              <option key={et} value={et}>
                {et}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Events Table / Stream */}
      <div className="max-h-64 overflow-y-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead className="sticky top-0 bg-[#070d1e] border-b border-slate-800 text-[10px] uppercase font-bold text-slate-400 font-mono tracking-wider z-10">
            <tr>
              <th className="py-2.5 px-3">Timestamp</th>
              <th className="py-2.5 px-3">Event Type</th>
              <th className="py-2.5 px-3">Agent</th>
              <th className="py-2.5 px-3">Request ID</th>
              <th className="py-2.5 px-3">State Transition</th>
              <th className="py-2.5 px-3">Reason Code</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {filteredEvents.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-xs text-slate-400 font-sans italic">
                  No telemetry events match the filter criteria.
                </td>
              </tr>
            ) : (
              filteredEvents.map((ev, idx) => (
                <tr key={ev.id || idx} className="hover:bg-slate-800/40 transition">
                  <td className="py-2 px-3 text-slate-400 text-[11px] whitespace-nowrap">
                    {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : 'N/A'}
                  </td>
                  <td className="py-2 px-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                        ev.category === 'COMPLETION'
                          ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                          : ev.category === 'FAILURE'
                          ? 'bg-red-500/10 text-red-300 border-red-500/30'
                          : ev.category === 'RECOVERY'
                          ? 'bg-purple-500/10 text-purple-300 border-purple-500/30'
                          : ev.category === 'ASSIGNMENT'
                          ? 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30'
                          : 'bg-slate-800 text-slate-300 border-slate-700'
                      }`}
                    >
                      {ev.event_type}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-white font-medium truncate max-w-[150px]">{ev.agent_id}</td>
                  <td className="py-2 px-3">
                    {ev.request_id ? (
                      <button
                        onClick={() => onSelectRequest && onSelectRequest(ev.request_id)}
                        className="text-cyan-400 hover:text-cyan-300 hover:underline font-bold"
                      >
                        {ev.request_id}
                      </button>
                    ) : (
                      <span className="text-slate-400">-</span>
                    )}
                  </td>
                  <td className="py-2 px-3 text-slate-400 text-[11px]">
                    {ev.previous_state || ev.new_state ? (
                      <span className="flex items-center space-x-1">
                        <span className="text-slate-400">{ev.previous_state || 'INIT'}</span>
                        <span>→</span>
                        <span className="text-emerald-400 font-bold">{ev.new_state || 'DONE'}</span>
                      </span>
                    ) : (
                      <span className="text-slate-400">STATE_STEADY</span>
                    )}
                  </td>
                  <td className="py-2 px-3 text-slate-400 text-[11px] truncate max-w-[180px]">
                    {ev.reason_code || 'RULE_BASED_EXECUTION'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
