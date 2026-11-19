import React, { useState } from 'react';
import { X, ShieldAlert, CheckCircle2, AlertTriangle, XCircle, ArrowUpRight } from 'lucide-react';

export const ReviewActionModal = ({ request, onClose, onSubmit }) => {
  if (!request) return null;

  const [decision, setDecision] = useState('REVIEW_COMPLETED');
  const [internalNote, setInternalNote] = useState('');
  const [reasonCode, setReasonCode] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const decisionOptions = [
    {
      key: 'REVIEW_COMPLETED',
      label: 'Complete Review (Concur)',
      desc: 'Clears review hold and advances request to verified stage.',
      icon: CheckCircle2,
      color: 'text-emerald-400 border-emerald-500/40 bg-emerald-950/20',
    },
    {
      key: 'ADDITIONAL_INFORMATION_REQUIRED',
      label: 'Require Additional Info',
      desc: 'Flags request as NEEDS_CORRECTION and alerts the customer.',
      icon: AlertTriangle,
      color: 'text-orange-400 border-orange-500/40 bg-orange-950/20',
    },
    {
      key: 'REVIEW_REJECTED',
      label: 'Reject Request',
      desc: 'Rejects request due to verification or compliance failure.',
      icon: XCircle,
      color: 'text-rose-400 border-rose-500/40 bg-rose-950/20',
    },
    {
      key: 'ESCALATED',
      label: 'Escalate to Senior Branch Head',
      desc: 'Sets priority to HIGH and retains supervisory hold.',
      icon: ArrowUpRight,
      color: 'text-cyan-400 border-cyan-500/40 bg-cyan-950/20',
    },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!internalNote.trim()) {
      setError('Please provide internal review notes explaining your rationale.');
      return;
    }

    setSubmitting(true);
    setError('');
    try {
      await onSubmit({
        decision,
        internal_note: internalNote.trim(),
        reason_code: reasonCode.trim() || undefined,
      });
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to submit review decision.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#0b132b] border border-slate-800 rounded-2xl w-full max-w-xl shadow-2xl text-slate-100 overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 bg-[#0d1733] flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Record Human Review Decision</h3>
              <p className="text-xs text-slate-400 font-mono">Request: {request.request_id}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5 text-xs">
          {error && (
            <div className="p-3 rounded-lg bg-red-950/60 border border-red-800 text-red-200">
              {error}
            </div>
          )}

          {/* Decision Selector */}
          <div className="space-y-2">
            <label className="font-semibold text-slate-300 block">Review Decision Outcome</label>
            <div className="space-y-2">
              {decisionOptions.map((opt) => {
                const Icon = opt.icon;
                const isSelected = decision === opt.key;
                return (
                  <label
                    key={opt.key}
                    onClick={() => setDecision(opt.key)}
                    className={`p-3 rounded-xl border flex items-start space-x-3 cursor-pointer transition ${
                      isSelected ? `${opt.color} ring-1 ring-emerald-500/40` : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <input
                      type="radio"
                      name="decision"
                      checked={isSelected}
                      onChange={() => setDecision(opt.key)}
                      className="mt-0.5 text-emerald-500 focus:ring-emerald-500"
                    />
                    <div className="flex-1">
                      <div className="flex items-center space-x-1.5 font-bold text-slate-100">
                        <Icon className="w-4 h-4" />
                        <span>{opt.label}</span>
                      </div>
                      <p className="text-[11px] text-slate-400 mt-0.5">{opt.desc}</p>
                    </div>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Reason Code (Optional) */}
          <div className="space-y-1.5">
            <label className="font-semibold text-slate-300 block">Reason Code / Categorization (Optional)</label>
            <input
              type="text"
              value={reasonCode}
              onChange={(e) => setReasonCode(e.target.value)}
              placeholder="e.g. KYC_VERIFIED, ID_MISMATCH, ADDRESS_DISCREPANCY"
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
            />
          </div>

          {/* Internal Review Note */}
          <div className="space-y-1.5">
            <label className="font-semibold text-slate-300 block">
              Internal Supervisory Review Note <span className="text-rose-400">*</span>
            </label>
            <textarea
              rows={4}
              value={internalNote}
              onChange={(e) => setInternalNote(e.target.value)}
              placeholder="Detailed justification, checks performed, and audit rationale..."
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
            />
            <span className="text-[10px] text-slate-500">
              Note: This review note is permanently recorded in compliance audit logs.
            </span>
          </div>

          {/* Buttons */}
          <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2 rounded-xl text-slate-300 hover:text-white bg-slate-900 hover:bg-slate-800 border border-slate-700 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 rounded-xl font-semibold text-slate-950 bg-emerald-400 hover:bg-emerald-300 transition flex items-center space-x-1.5 shadow-lg shadow-emerald-500/20"
            >
              {submitting ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin"></div>
                  <span>Recording...</span>
                </>
              ) : (
                <span>Confirm Decision</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
