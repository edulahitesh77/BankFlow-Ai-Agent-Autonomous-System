import React, { useState, useEffect } from 'react';
import {
  X,
  Minus,
  Maximize2,
  Workflow,
  Clock,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  RotateCw,
  Search,
  User,
  ShieldAlert,
  Layers,
  Database,
  Cpu,
} from 'lucide-react';
import {
  fetchVisualizerRecentRequests,
  fetchVisualizerRequestJourney,
} from '../../../../api/auth';

export const RequestJourneyDrawer = ({ isOpen, initialRequestId, onClose, onSelectRequest }) => {
  const [recentRequests, setRecentRequests] = useState([]);
  const [selectedRequestId, setSelectedRequestId] = useState(initialRequestId || '');
  const [journeyData, setJourneyData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isMinimized, setIsMinimized] = useState(false);

  // Sync initialRequestId when updated from outside (e.g. clicking an event or agent)
  useEffect(() => {
    if (initialRequestId) {
      setSelectedRequestId(initialRequestId);
      setIsMinimized(false);
    }
  }, [initialRequestId]);

  // Load concise list of recent requests (reduced to 6 top requests as requested)
  useEffect(() => {
    if (!isOpen) return;
    const loadRequests = async () => {
      try {
        const list = await fetchVisualizerRecentRequests(6);
        const conciseList = list.slice(0, 6);
        setRecentRequests(conciseList);
        if (!selectedRequestId && conciseList.length > 0) {
          setSelectedRequestId(conciseList[0].request_id);
        }
      } catch (err) {
        console.error('Failed to load recent requests for journey inspector:', err);
      }
    };
    loadRequests();
  }, [isOpen]);

  // When selectedRequestId changes, fetch its journey
  useEffect(() => {
    if (!isOpen || !selectedRequestId) return;
    const loadJourney = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchVisualizerRequestJourney(selectedRequestId);
        setJourneyData(data);
      } catch (err) {
        setError(err.message || 'Failed to fetch request journey.');
      } finally {
        setLoading(false);
      }
    };
    loadJourney();
  }, [isOpen, selectedRequestId]);

  if (!isOpen) return null;

  // Minimized Floating Pill View (leaves canvas completely clear)
  if (isMinimized) {
    return (
      <div className="fixed bottom-6 right-6 z-50 flex items-center space-x-2.5 p-2 px-3 rounded-2xl bg-[#091126]/95 border border-cyan-500/40 shadow-2xl backdrop-blur-md animate-fadeIn">
        <div className="flex items-center space-x-2">
          <Workflow className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-mono font-bold text-white truncate max-w-[150px]">
            {selectedRequestId || 'Request Journey'}
          </span>
        </div>
        <button
          onClick={() => setIsMinimized(false)}
          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 transition"
          title="Expand Journey Inspector"
        >
          <Maximize2 className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          title="Close Inspector"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    );
  }

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-lg bg-[#091126]/98 backdrop-blur-xl border-l border-slate-800 shadow-2xl flex flex-col transform transition-transform duration-300">
      {/* Header with Minimize and Close Buttons */}
      <div className="p-4 sm:p-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Workflow className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide">Request Journey Inspector</h3>
            <span className="text-xs text-slate-400 font-mono">End-to-End Multi-Agent Timeline</span>
          </div>
        </div>

        <div className="flex items-center space-x-1.5">
          <button
            onClick={() => setIsMinimized(true)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-cyan-300 hover:bg-slate-800 transition"
            title="Minimize to Floating Pill"
          >
            <Minus className="w-4 h-4" />
          </button>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            title="Close Drawer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Concise Request Selector (Limited to top 6 recent requests) */}
      <div className="p-4 border-b border-slate-800/80 bg-slate-900/40 space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block">
            Select Banking Request ({recentRequests.length} Recent)
          </label>
          <span className="text-[10px] text-cyan-400 font-mono font-medium">Top Recent</span>
        </div>
        <select
          value={selectedRequestId}
          onChange={(e) => setSelectedRequestId(e.target.value)}
          className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
        >
          {recentRequests.map((r) => (
            <option key={r.request_id} value={r.request_id}>
              {r.request_id} • {r.service_type} ({r.request_status})
            </option>
          ))}
        </select>
      </div>

      {/* Content Scroll */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4">
        {loading ? (
          <div className="py-20 text-center space-y-3">
            <div className="w-8 h-8 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p className="text-xs text-slate-400 font-medium">Reconstructing journey milestones...</p>
          </div>
        ) : error ? (
          <div className="p-4 rounded-xl bg-red-950/60 border border-red-800 text-xs text-red-200">
            {error}
          </div>
        ) : journeyData ? (
          <>
            {/* Summary Overview Card */}
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <span className="font-mono text-sm font-bold text-white block">
                    {journeyData.request_id}
                  </span>
                  <div className="text-xs text-slate-400 flex items-center space-x-2 mt-0.5">
                    <span>{journeyData.customer_name}</span>
                    <span>•</span>
                    <span className="text-cyan-400 font-medium">{journeyData.service_type}</span>
                  </div>
                </div>

                <span
                  className={`px-2.5 py-0.5 rounded-full text-xs font-bold font-mono border ${
                    journeyData.status === 'COMPLETED'
                      ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                      : journeyData.status === 'HUMAN_REVIEW'
                      ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                      : journeyData.status === 'NEEDS_CORRECTION'
                      ? 'bg-orange-500/20 text-orange-300 border-orange-500/40'
                      : 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                  }`}
                >
                  {journeyData.status}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs pt-1">
                <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-850">
                  <span className="text-[10px] text-slate-400 block font-semibold uppercase">Total Milestones</span>
                  <span className="text-white font-bold font-mono">{journeyData.step_count} Steps</span>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-850">
                  <span className="text-[10px] text-slate-400 block font-semibold uppercase">Total Duration</span>
                  <span className="text-emerald-400 font-bold font-mono">
                    {journeyData.total_duration_seconds > 0
                      ? `${journeyData.total_duration_seconds}s`
                      : 'In Flight'}
                  </span>
                </div>
              </div>
            </div>

            {/* Stepper Timeline */}
            <div className="space-y-3 relative pl-4 border-l-2 border-slate-800 ml-2">
              {journeyData.steps.map((st, idx) => {
                const isSuccess = st.outcome === 'SUCCESS';
                const isException = st.outcome === 'EXCEPTION';
                const isFail = st.outcome === 'FAILED';

                return (
                  <div key={idx} className="relative group">
                    {/* Circle Node on Timeline Line */}
                    <div
                      className={`absolute -left-[25px] top-1.5 w-4 h-4 rounded-full border-2 bg-[#091126] flex items-center justify-center text-[9px] font-bold ${
                        isFail
                          ? 'border-red-500 text-red-400'
                          : isException
                          ? 'border-amber-500 text-amber-400'
                          : 'border-emerald-500 text-emerald-400'
                      }`}
                    >
                      {st.step}
                    </div>

                    {/* Step Card */}
                    <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition space-y-2">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <h4 className="text-xs font-bold text-white leading-tight">{st.title}</h4>
                          <div className="flex items-center space-x-1.5 text-[11px] text-slate-400 font-mono mt-0.5">
                            <span className="text-cyan-400">{st.agent_name || st.agent_id}</span>
                            <span>•</span>
                            <span className="text-slate-400">{st.stage}</span>
                          </div>
                        </div>

                        <span className="text-[10px] text-slate-400 font-mono">
                          {st.timestamp ? new Date(st.timestamp).toLocaleTimeString() : 'N/A'}
                        </span>
                      </div>

                      <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-850 flex items-center justify-between text-[11px]">
                        <div className="flex items-center space-x-1.5 text-slate-400">
                          <span className="text-[9px] uppercase font-semibold">Reason:</span>
                          <span className="font-mono text-emerald-400 truncate max-w-[200px]">{st.reason_code}</span>
                        </div>
                        {st.duration_seconds > 0 && (
                          <div className="flex items-center space-x-1 text-slate-400 font-mono text-[10px]">
                            <Clock className="w-3 h-3" />
                            <span>+{st.duration_seconds}s</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        ) : null}
      </div>

      {/* Footer with Minimize and Close Options */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/80 flex items-center justify-between">
        <button
          onClick={() => setIsMinimized(true)}
          className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-xl text-xs font-semibold text-cyan-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition"
        >
          <Minus className="w-3.5 h-3.5" />
          <span>Minimize Drawer</span>
        </button>

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
