import React, { useState, useEffect } from 'react';
import {
  Search,
  CheckCircle2,
  Clock,
  AlertTriangle,
  XCircle,
  FileText,
  UserCheck,
  Cpu,
  Layers,
  ArrowRight,
  Edit3,
  Send,
  AlertCircle,
  Calendar,
  Building,
  Info,
} from 'lucide-react';
import { fetchServiceRequestDetail, correctServiceRequest } from '../../../api/auth';
import { getStatusBadge } from './DashboardOverview';

export const TrackRequestTab = ({ selectedRequestId, onNavigateTab }) => {
  const [searchId, setSearchId] = useState(selectedRequestId || '');
  const [requestDetail, setRequestDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Correction form state
  const [showCorrectionForm, setShowCorrectionForm] = useState(false);
  const [correctionPayload, setCorrectionPayload] = useState({});
  const [correctionNotes, setCorrectionNotes] = useState('');
  const [correctionSubmitting, setCorrectionSubmitting] = useState(false);
  const [correctionMsg, setCorrectionMsg] = useState('');

  const loadDetail = async (idToFetch) => {
    if (!idToFetch || !idToFetch.trim()) return;
    setLoading(true);
    setError('');
    setCorrectionMsg('');
    try {
      const data = await fetchServiceRequestDetail(idToFetch.trim());
      setRequestDetail(data);
      setCorrectionPayload(data.payload || {});
      setShowCorrectionForm(data.request_status === 'NEEDS_CORRECTION');
    } catch (err) {
      setError(err.message || 'Request not found or unauthorized.');
      setRequestDetail(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedRequestId) {
      setSearchId(selectedRequestId);
      loadDetail(selectedRequestId);
    }
  }, [selectedRequestId]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchId) loadDetail(searchId);
  };

  const handleCorrectionSubmit = async (e) => {
    e.preventDefault();
    setCorrectionSubmitting(true);
    setCorrectionMsg('');
    setError('');
    try {
      const updated = await correctServiceRequest(requestDetail.request_id, {
        payload: correctionPayload,
        correction_notes: correctionNotes || undefined,
      });
      setRequestDetail(updated);
      setCorrectionMsg('Correction submitted successfully! Request status reset to NEW for re-evaluation.');
      setShowCorrectionForm(false);
    } catch (err) {
      setError(err.message || 'Failed to submit correction.');
    } finally {
      setCorrectionSubmitting(false);
    }
  };

  // Determine stage active index (0 to 4)
  const getStageIndex = (status) => {
    switch (status) {
      case 'NEW':
        return 0; // Stage 1 active (Request Submitted)
      case 'CLASSIFIED':
      case 'QUEUED':
        return 1; // Stage 2 active (Intake Classification)
      case 'VERIFIED':
        return 2; // Stage 3 active (Verification)
      case 'IN_SERVICE':
        return 3; // Stage 4 active (Service Processing)
      case 'COMPLETED':
        return 4; // Stage 5 complete (Final Disposition)
      case 'NEEDS_CORRECTION':
      case 'HUMAN_REVIEW':
      case 'REJECTED_INPUT':
      case 'FAILED':
        return 2; // Exception branch
      default:
        return 0;
    }
  };

  const stages = [
    { title: 'Request Submitted', subtitle: 'Awaiting Intake', icon: FileText },
    { title: 'Intake Classification', subtitle: 'Service Categorization', icon: Cpu },
    { title: 'Verification', subtitle: 'Identity & Completeness', icon: UserCheck },
    { title: 'Service Processing', subtitle: 'Autonomous Execution', icon: Layers },
    { title: 'Final Disposition', subtitle: 'Fulfillment & Audit', icon: CheckCircle2 },
  ];

  const currentStageIdx = requestDetail ? getStageIndex(requestDetail.request_status) : 0;
  const isException = requestDetail && ['NEEDS_CORRECTION', 'HUMAN_REVIEW', 'REJECTED_INPUT', 'FAILED'].includes(requestDetail.request_status);

  return (
    <div className="space-y-6 animate-fade-in max-w-5xl mx-auto">
      {/* Header and Search */}
      <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-sm space-y-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Track Service Request Status</h2>
          <p className="text-xs text-slate-500 mt-1">
            Real-time multi-agent processing pipeline inspector backed by PostgreSQL
          </p>
        </div>

        <form onSubmit={handleSearchSubmit} className="flex gap-3">
          <div className="relative flex-1">
            <input
              type="text"
              required
              placeholder="Enter Request ID (e.g. BFA-REQ-2026-00001)..."
              value={searchId}
              onChange={(e) => setSearchId(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-xs sm:text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3 pointer-events-none" />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold shadow-md shadow-blue-500/20 transition disabled:opacity-60"
          >
            {loading ? 'Searching...' : 'Track Request'}
          </button>
        </form>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 flex items-center space-x-3 text-red-700 text-xs animate-fade-in">
          <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Success Notification */}
      {correctionMsg && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center space-x-3 text-emerald-800 text-xs font-medium animate-fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          <span>{correctionMsg}</span>
        </div>
      )}

      {/* Request Details Card */}
      {requestDetail && (
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-sm space-y-8 animate-fade-in">
          {/* Top Metadata Header */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-100 pb-6">
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-mono text-xl font-extrabold text-slate-900">
                  {requestDetail.request_id}
                </span>
                <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getStatusBadge(requestDetail.request_status)}`}>
                  {requestDetail.request_status}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Service: <strong className="text-slate-800">{requestDetail.service_type.replace(/_/g, ' ')}</strong> • Priority: {requestDetail.priority}
              </p>
            </div>

            <div className="text-right text-xs text-slate-500 space-y-0.5">
              <div>Version: <span className="font-mono font-bold text-slate-800">v{requestDetail.assignment_version}</span></div>
              <div>Submitted: {new Date(requestDetail.created_at).toLocaleString()}</div>
              <div>Last Updated: {new Date(requestDetail.updated_at).toLocaleString()}</div>
            </div>
          </div>

          {/* Customer Delay/Monitoring Banner (Phase 8 Fault Tolerance) */}
          {requestDetail.customer_status_message && (
            <div className="p-4 rounded-2xl border border-blue-200 bg-blue-50/90 text-blue-900 text-xs flex items-center space-x-3 animate-fade-in">
              <Clock className="w-5 h-5 text-blue-600 flex-shrink-0" />
              <div>
                <span className="font-bold">{requestDetail.customer_status_message}</span>
                <span className="text-blue-700 ml-1">
                  Thank you for your patience while our automated verification processes ensure your account security.
                </span>
              </div>
            </div>
          )}

          {/* Exception State Banner */}
          {isException && (
            <div
              className={`p-5 rounded-2xl border flex items-start space-x-3.5 text-xs ${
                requestDetail.request_status === 'NEEDS_CORRECTION'
                  ? 'bg-orange-50 border-orange-200 text-orange-950'
                  : requestDetail.request_status === 'HUMAN_REVIEW'
                  ? 'bg-yellow-50 border-yellow-200 text-yellow-950'
                  : 'bg-rose-50 border-rose-200 text-rose-950'
              }`}
            >
              <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div className="space-y-1.5 flex-1">
                <div className="font-bold text-sm">
                  {requestDetail.request_status === 'NEEDS_CORRECTION'
                    ? 'Action Required: Request Needs Customer Correction'
                    : requestDetail.request_status === 'HUMAN_REVIEW'
                    ? 'Supervisor Escalation: Under Human Staff Oversight'
                    : 'Workflow Disposition: Request Rejected / Failed'}
                </div>
                <div>
                  Reason Code:{' '}
                  <code className="px-2 py-0.5 bg-white/80 rounded font-mono font-bold">
                    {requestDetail.reason_code || 'INCOMPLETE_OR_AMBIGUOUS_DATA'}
                  </code>
                </div>
                {requestDetail.request_status === 'NEEDS_CORRECTION' && !showCorrectionForm && (
                  <button
                    onClick={() => setShowCorrectionForm(true)}
                    className="mt-2 inline-flex items-center space-x-1.5 px-3.5 py-1.5 bg-orange-600 hover:bg-orange-700 text-white rounded-lg font-semibold text-xs transition"
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                    <span>Open Correction Editor</span>
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Visual Progress Stepper */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Multi-Agent Processing Lifecycle Stage
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 pt-2">
              {stages.map((stg, idx) => {
                const Icon = stg.icon;
                const isPassed = currentStageIdx > idx && !isException;
                const isCurrent = currentStageIdx === idx && !isException;
                const isFailed = isException && currentStageIdx === idx;

                return (
                  <div
                    key={stg.title}
                    className={`p-4 rounded-2xl border text-center space-y-2 transition ${
                      isPassed
                        ? 'bg-emerald-50/70 border-emerald-200 text-emerald-900'
                        : isCurrent
                        ? 'bg-blue-50 border-blue-500 shadow-sm text-blue-900 ring-2 ring-blue-500/20'
                        : isFailed
                        ? 'bg-orange-50 border-orange-400 text-orange-900 ring-2 ring-orange-400/20'
                        : 'bg-slate-50 border-slate-200 text-slate-400'
                    }`}
                  >
                    <div
                      className={`w-9 h-9 rounded-xl flex items-center justify-center mx-auto ${
                        isPassed
                          ? 'bg-emerald-600 text-white'
                          : isCurrent
                          ? 'bg-blue-600 text-white'
                          : isFailed
                          ? 'bg-orange-500 text-white'
                          : 'bg-slate-200 text-slate-500'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="text-xs font-bold leading-tight">{stg.title}</div>
                    <div className="text-[10px] leading-tight text-slate-500">{stg.subtitle}</div>
                  </div>
                );
              })}
            </div>

            <div className="p-3 bg-slate-50 rounded-xl text-xs text-slate-600 flex items-center justify-between">
              <span>Current Status Stage:</span>
              <span className="font-semibold text-slate-900">{requestDetail.current_stage}</span>
            </div>
          </div>

          {/* Interactive Correction Form (when in NEEDS_CORRECTION state) */}
          {showCorrectionForm && requestDetail.request_status === 'NEEDS_CORRECTION' && (
            <div className="p-6 rounded-3xl bg-orange-50/60 border border-orange-200 space-y-4 animate-fade-in">
              <div className="flex items-center space-x-2 text-orange-900 font-bold text-sm">
                <Edit3 className="w-4 h-4 text-orange-600" />
                <span>Submit Request Corrections</span>
              </div>
              <p className="text-xs text-orange-800">
                Update the parameters below to resolve the exception flag. Upon submitting, the request will be reset to status <strong>NEW</strong> for intake re-evaluation.
              </p>

              <form onSubmit={handleCorrectionSubmit} className="space-y-4 bg-white p-5 rounded-2xl border border-orange-200">
                {requestDetail.service_type === 'CHEQUE_BOOK' && (
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Correct Number of Cheque Leaves:
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      {[25, 50, 100].map((leaves) => (
                        <button
                          key={leaves}
                          type="button"
                          onClick={() => setCorrectionPayload((p) => ({ ...p, cheque_leaves: leaves }))}
                          className={`py-2 text-xs font-bold rounded-lg border ${
                            correctionPayload.cheque_leaves === leaves
                              ? 'bg-orange-600 text-white border-orange-600'
                              : 'bg-slate-50 text-slate-700 border-slate-200'
                          }`}
                        >
                          {leaves} Leaves
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {requestDetail.service_type === 'DEBIT_CARD_REPLACEMENT' && (
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Correct Replacement Reason:
                    </label>
                    <select
                      value={correctionPayload.replacement_reason || 'Damaged Card'}
                      onChange={(e) => setCorrectionPayload((p) => ({ ...p, replacement_reason: e.target.value }))}
                      className="w-full text-xs p-2.5 bg-slate-50 border rounded-lg"
                    >
                      <option value="Damaged Card">Damaged Card</option>
                      <option value="Lost Card (simulation only)">Lost Card (simulation only)</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>
                )}

                {requestDetail.service_type === 'ADDRESS_UPDATE' && (
                  <div className="space-y-3">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1">Correct Street Address:</label>
                      <input
                        type="text"
                        required
                        value={correctionPayload.new_synthetic_address || ''}
                        onChange={(e) => setCorrectionPayload((p) => ({ ...p, new_synthetic_address: e.target.value }))}
                        className="w-full text-xs p-2 bg-slate-50 border rounded-lg"
                      />
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                      <input
                        type="text"
                        placeholder="City"
                        value={correctionPayload.city || ''}
                        onChange={(e) => setCorrectionPayload((p) => ({ ...p, city: e.target.value }))}
                        className="text-xs p-2 bg-slate-50 border rounded-lg"
                      />
                      <input
                        type="text"
                        placeholder="State"
                        value={correctionPayload.state || ''}
                        onChange={(e) => setCorrectionPayload((p) => ({ ...p, state: e.target.value }))}
                        className="text-xs p-2 bg-slate-50 border rounded-lg"
                      />
                      <input
                        type="text"
                        placeholder="Postal Code"
                        value={correctionPayload.postal_code || ''}
                        onChange={(e) => setCorrectionPayload((p) => ({ ...p, postal_code: e.target.value }))}
                        className="text-xs p-2 bg-slate-50 border rounded-lg"
                      />
                    </div>
                  </div>
                )}

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Customer Explanation / Correction Notes:
                  </label>
                  <textarea
                    rows={2}
                    required
                    placeholder="Describe the corrections made..."
                    value={correctionNotes}
                    onChange={(e) => setCorrectionNotes(e.target.value)}
                    className="w-full text-xs p-2 bg-slate-50 border rounded-lg"
                  />
                </div>

                <div className="flex justify-end space-x-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowCorrectionForm(false)}
                    className="px-3.5 py-2 text-xs font-semibold text-slate-600 bg-slate-100 rounded-lg"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={correctionSubmitting}
                    className="inline-flex items-center space-x-1.5 px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white text-xs font-semibold rounded-lg shadow-sm disabled:opacity-60"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>{correctionSubmitting ? 'Submitting...' : 'Submit Correction'}</span>
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Form Payload Parameters Card */}
          <div className="bg-slate-50 rounded-2xl p-5 border border-slate-200 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Submitted Service Parameters
            </h4>
            {requestDetail.payload && Object.keys(requestDetail.payload).length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                {Object.entries(requestDetail.payload).map(([k, v]) => (
                  <div key={k} className="p-2.5 bg-white rounded-xl border border-slate-100">
                    <span className="font-semibold text-slate-500 capitalize block text-[10px]">
                      {k.replace(/_/g, ' ')}
                    </span>
                    <span className="font-medium text-slate-800 break-words">
                      {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400">No service parameters stored.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
