import React, { useState } from 'react';
import { X, AlertTriangle, Send } from 'lucide-react';

export const CorrectionActionModal = ({ request, onClose, onSubmit }) => {
  if (!request) return null;

  const [reason, setReason] = useState('Document Illegible');
  const [instruction, setInstruction] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const commonReasons = [
    'Document Illegible',
    'Address Mismatch',
    'Invalid Leaf Count Selection',
    'Incomplete Identification Reference',
    'Other Discrepancy',
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!instruction.trim()) {
      setError('Please provide clear actionable instructions for the customer.');
      return;
    }

    setSubmitting(true);
    setError('');
    try {
      await onSubmit({
        correction_reason: reason,
        customer_instruction: instruction.trim(),
      });
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to request correction.');
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
            <div className="w-9 h-9 rounded-xl bg-orange-500/10 border border-orange-500/30 flex items-center justify-center text-orange-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Issue Customer Correction Request</h3>
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

          {/* Reason Selection */}
          <div className="space-y-1.5">
            <label className="font-semibold text-slate-300 block">Correction Reason Category</label>
            <select
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-orange-500"
            >
              {commonReasons.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>

          {/* Customer Instruction */}
          <div className="space-y-1.5">
            <label className="font-semibold text-slate-300 block">
              Customer Instructions <span className="text-rose-400">*</span>
            </label>
            <textarea
              rows={4}
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
              placeholder="Explain clearly what information or document the customer must update..."
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-orange-500"
            />
            <p className="text-[11px] text-slate-400">
              This message will be instantly delivered to the customer via an in-app notification, allowing them to edit and resubmit their request.
            </p>
          </div>

          {/* Actions */}
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
              className="px-5 py-2 rounded-xl font-semibold text-slate-950 bg-orange-400 hover:bg-orange-300 transition flex items-center space-x-1.5 shadow-lg shadow-orange-500/20"
            >
              {submitting ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin"></div>
                  <span>Notifying...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Send Correction Request</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
