import React, { useState, useEffect } from 'react';
import {
  X,
  ShieldCheck,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  RotateCw,
  Search,
  Filter,
  Layers,
  Clock,
  Terminal,
  Activity,
} from 'lucide-react';
import { fetchVisualizerDecisions } from '../../../../api/auth';

export const DecisionInspectorModal = ({ isOpen, onClose, onSelectRequest }) => {
  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState(null);

  const loadDecisions = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchVisualizerDecisions(50);
      setDecisions(data);
    } catch (err) {
      setError(err.message || 'Failed to load decision audit trail.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadDecisions();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const filteredDecisions = decisions.filter((d) => {
    const matchesFilter = filterType === 'ALL' || d.decision_type === filterType;
    const matchesSearch =
      !searchTerm ||
      d.request_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.agent_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.reason_code?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-950/80 backdrop-blur-md">
      <div className="w-full max-w-4xl max-h-[85vh] bg-[#091126] border border-slate-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <Terminal className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-base font-bold text-white">Agent Decision Inspector</h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                  Deterministic Rule-Based Engine
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Authentic audit records of agent decisions, reason codes, input criteria, and selected actions.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Filters & Search Toolbar */}
        <div className="p-4 border-b border-slate-800/80 bg-slate-900/40 flex flex-wrap items-center justify-between gap-3">
          <div className="relative flex-1 min-w-[200px] max-w-sm">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by Request ID, Agent, or Reason..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
            />
          </div>

          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="ALL">All Decision Types</option>
              <option value="INTAKE_VALIDATION">Intake Validation</option>
              <option value="DISPATCH_ALLOCATION">Dispatch & Least-Loaded Policy</option>
              <option value="COMPLIANCE_VERIFICATION">Compliance Verification</option>
              <option value="SERVICE_EXECUTION">Service Execution</option>
              <option value="FAULT_TOLERANCE_SUPERVISION">Fault Supervision</option>
              <option value="EXCEPTION_GATE">Human Review Exception</option>
            </select>

            <button
              onClick={loadDecisions}
              className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
            >
              Refresh
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-3.5">
          {loading ? (
            <div className="py-16 text-center space-y-3">
              <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p className="text-xs text-slate-400 font-medium">Querying authoritative decision records...</p>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-red-950/60 border border-red-800 text-xs text-red-200">
              {error}
            </div>
          ) : filteredDecisions.length === 0 ? (
            <div className="py-16 text-center text-xs text-slate-400">
              No decision records matched the criteria.
            </div>
          ) : (
            filteredDecisions.map((dec) => (
              <div
                key={dec.decision_id}
                className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition space-y-2.5"
              >
                {/* Decision Header */}
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs font-bold text-indigo-400">{dec.decision_id}</span>
                    <span className="text-slate-500">•</span>
                    <span className="text-xs font-bold text-white">{dec.agent_name || dec.agent_id}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">
                      {dec.decision_type}
                    </span>
                  </div>

                  <span className="text-[10px] text-slate-400 font-mono">
                    {new Date(dec.timestamp).toLocaleTimeString()}
                  </span>
                </div>

                {/* Grid of decision details */}
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                  <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-850">
                    <span className="text-[9px] uppercase text-slate-400 font-semibold block">Reason Code</span>
                    <span className="font-mono text-emerald-400 font-semibold truncate block mt-0.5">
                      {dec.reason_code}
                    </span>
                  </div>

                  <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-850">
                    <span className="text-[9px] uppercase text-slate-400 font-semibold block">Selected Action</span>
                    <span className="font-mono text-cyan-300 font-semibold truncate block mt-0.5">
                      {dec.selected_action}
                    </span>
                  </div>

                  <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-850">
                    <span className="text-[9px] uppercase text-slate-400 font-semibold block">Decision Result</span>
                    <span className="font-mono text-slate-200 font-semibold truncate block mt-0.5">
                      {dec.result}
                    </span>
                  </div>

                  <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-850 flex items-center justify-between">
                    <div>
                      <span className="text-[9px] uppercase text-slate-400 font-semibold block">Request</span>
                      <span className="font-mono text-white font-bold block mt-0.5">{dec.request_id}</span>
                    </div>
                    {onSelectRequest && (
                      <button
                        onClick={() => {
                          onClose();
                          onSelectRequest(dec.request_id);
                        }}
                        className="px-2 py-1 text-[10px] font-semibold rounded bg-indigo-500/20 text-indigo-300 hover:bg-indigo-500/30 border border-indigo-500/40 transition"
                      >
                        Track
                      </button>
                    )}
                  </div>
                </div>

                {/* Input Conditions */}
                <div className="text-[11px] text-slate-400 bg-slate-950/40 p-2 rounded-lg border border-slate-850 flex items-center justify-between">
                  <span className="text-slate-500 font-medium mr-2">Input Conditions:</span>
                  <span className="font-mono text-slate-300 truncate">{dec.input_conditions}</span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/60 flex items-center justify-between">
          <div className="text-xs text-slate-400 font-mono">
            Showing <span className="text-white font-bold">{filteredDecisions.length}</span> authentic decision logs
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
