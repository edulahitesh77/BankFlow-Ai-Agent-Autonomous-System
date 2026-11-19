import React, { useState } from 'react';
import {
  X,
  ShieldAlert,
  User,
  CreditCard,
  Building,
  Calendar,
  Clock,
  CheckCircle2,
  AlertTriangle,
  FileText,
  AlertCircle,
  ArrowRight,
  Send,
  HelpCircle,
} from 'lucide-react';

export const RequestDetailModal = ({
  request,
  onClose,
  onOpenReview,
  onOpenCorrection,
  onInspectCustomer,
}) => {
  if (!request) return null;

  const payload = request.payload || {};

  const lifecycleStages = [
    { key: 'NEW', label: 'Submitted', desc: 'Customer submission' },
    { key: 'CLASSIFIED', label: 'Classified', desc: 'Intake classification' },
    { key: 'QUEUED', label: 'Queued', desc: 'Awaiting agent dispatch' },
    { key: 'VERIFIED', label: 'Verified', desc: 'Rules & Fraud check' },
    { key: 'IN_SERVICE', label: 'In Service', desc: 'Backend service execution' },
    { key: 'COMPLETED', label: 'Completed', desc: 'Workflow fulfilled' },
  ];

  const getStageIndex = (status) => {
    switch (status) {
      case 'NEW':
        return 0;
      case 'CLASSIFIED':
        return 1;
      case 'QUEUED':
        return 2;
      case 'VERIFIED':
        return 3;
      case 'IN_SERVICE':
        return 4;
      case 'COMPLETED':
        return 5;
      default:
        return 0;
    }
  };

  const currentStageIdx = getStageIndex(request.request_status);
  const isExceptionStatus = [
    'NEEDS_CORRECTION',
    'HUMAN_REVIEW',
    'REJECTED_INPUT',
    'FAILED',
  ].includes(request.request_status);

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#0b132b] border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl text-slate-100 overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 bg-[#0d1733] flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-lg font-bold text-white font-mono tracking-tight">{request.request_id}</h3>
                <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-slate-800 border border-slate-700 text-slate-300">
                  v{request.assignment_version}
                </span>
                <span
                  className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${
                    request.request_status === 'COMPLETED'
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                      : request.request_status === 'HUMAN_REVIEW'
                      ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                      : request.request_status === 'NEEDS_CORRECTION'
                      ? 'bg-orange-500/10 text-orange-400 border-orange-500/30'
                      : request.request_status === 'REJECTED_INPUT' || request.request_status === 'FAILED'
                      ? 'bg-red-500/10 text-red-400 border-red-500/30'
                      : 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30'
                  }`}
                >
                  {request.request_status.replace('_', ' ')}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Service: <span className="text-emerald-400 font-semibold">{request.service_type.replace(/_/g, ' ')}</span> • Submitted on{' '}
                {new Date(request.created_at).toLocaleString()}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-sm">
          {/* Exception Banner if applicable */}
          {isExceptionStatus && (
            <div
              className={`p-4 rounded-xl border flex items-start space-x-3 ${
                request.request_status === 'HUMAN_REVIEW'
                  ? 'bg-amber-950/40 border-amber-800/80 text-amber-200'
                  : request.request_status === 'NEEDS_CORRECTION'
                  ? 'bg-orange-950/40 border-orange-800/80 text-orange-200'
                  : 'bg-red-950/40 border-red-800/80 text-red-200'
              }`}
            >
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-bold text-sm">
                  {request.request_status === 'HUMAN_REVIEW'
                    ? 'Supervisory Action Required: Human Review'
                    : request.request_status === 'NEEDS_CORRECTION'
                    ? 'Customer Action Pending: Needs Correction'
                    : 'Request Rejected'}
                </h4>
                <p className="text-xs mt-1 opacity-90">
                  {request.reason_code ? `Reason Code: ${request.reason_code}` : 'Awaiting supervisory intervention or customer response.'}
                </p>
              </div>
            </div>
          )}

          {/* Visual Lifecycle Stepper */}
          <div className="bg-[#0f1a3a] border border-slate-800 rounded-xl p-5">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">Request Lifecycle Pipeline</h4>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              {lifecycleStages.map((stage, idx) => {
                const isPassed = !isExceptionStatus && idx < currentStageIdx;
                const isCurrent = !isExceptionStatus && idx === currentStageIdx;

                return (
                  <div
                    key={stage.key}
                    className={`p-3 rounded-xl border flex flex-col items-center text-center transition ${
                      isPassed
                        ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                        : isCurrent
                        ? 'bg-cyan-500/15 border-cyan-500/50 text-white shadow-lg ring-1 ring-cyan-500/30'
                        : 'bg-slate-900/60 border-slate-800 text-slate-500'
                    }`}
                  >
                    <div
                      className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold mb-1.5 ${
                        isPassed
                          ? 'bg-emerald-500 text-slate-950'
                          : isCurrent
                          ? 'bg-cyan-400 text-slate-950 animate-pulse'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {isPassed ? <CheckCircle2 className="w-4 h-4" /> : idx + 1}
                    </div>
                    <span className="text-xs font-bold leading-tight">{stage.label}</span>
                    <span className="text-[10px] text-slate-400 mt-0.5">{stage.desc}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Two-Column Grid: Customer Info & Request Metadata */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Customer Information Card */}
            <div className="bg-[#0f1a3a] border border-slate-800 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center space-x-2 text-white font-semibold">
                  <User className="w-4 h-4 text-emerald-400" />
                  <span>Customer Information</span>
                </div>
                {onInspectCustomer && (
                  <button
                    onClick={() => onInspectCustomer(request.customer_id)}
                    className="text-xs text-emerald-400 hover:text-emerald-300 font-medium underline"
                  >
                    View Record →
                  </button>
                )}
              </div>

              <div className="grid grid-cols-2 gap-y-3 text-xs">
                <div>
                  <span className="text-slate-400 block">Full Name</span>
                  <span className="font-semibold text-white">{request.customer_name}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Customer Code</span>
                  <span className="font-mono text-emerald-400 font-semibold">{request.customer_code}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Email Address</span>
                  <span className="text-slate-200">{request.customer_email}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Phone</span>
                  <span className="text-slate-200">{request.customer_phone || 'Not recorded'}</span>
                </div>
                <div className="col-span-2">
                  <span className="text-slate-400 block">Home Branch</span>
                  <span className="text-slate-200">{request.customer_branch || 'Central Digital Branch'}</span>
                </div>
              </div>
            </div>

            {/* Request Details & Target Account */}
            <div className="bg-[#0f1a3a] border border-slate-800 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center space-x-2 text-white font-semibold">
                  <CreditCard className="w-4 h-4 text-cyan-400" />
                  <span>Request Metadata</span>
                </div>
                <span
                  className={`text-[11px] font-bold px-2 py-0.5 rounded ${
                    request.priority === 'HIGH' || request.priority === 'URGENT'
                      ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                      : 'bg-slate-800 text-slate-300'
                  }`}
                >
                  Priority: {request.priority}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-y-3 text-xs">
                <div>
                  <span className="text-slate-400 block">Target Account</span>
                  <span className="font-mono text-cyan-300 font-semibold">
                    {request.account_number || 'N/A (General Application)'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block">Account Type</span>
                  <span className="text-slate-200">{request.account_type || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Assigned Agent</span>
                  <span className="text-slate-300 font-mono">
                    {request.assigned_agent_code || 'Pending Multi-Agent Intake'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block">Review Required</span>
                  <span className={request.review_required ? 'text-amber-400 font-bold' : 'text-slate-400'}>
                    {request.review_required ? 'YES (Human Gate)' : 'NO'}
                  </span>
                </div>
                <div className="col-span-2">
                  <span className="text-slate-400 block">Completeness Status</span>
                  <span className="text-slate-200">{request.completeness_status || 'VERIFIED'}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Service-Specific Parameters Card */}
          <div className="bg-[#0f1a3a] border border-slate-800 rounded-xl p-5 space-y-4">
            <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">
              Submitted Service Parameters ({request.service_type.replace(/_/g, ' ')})
            </h4>

            {request.service_type === 'CHEQUE_BOOK' && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800">
                  <span className="text-slate-400 block">Cheque Leaves Requested</span>
                  <span className="text-base font-bold text-white mt-1 block">
                    {payload.number_of_leaves ? `${payload.number_of_leaves} Leaves` : 'Standard (25)'}
                  </span>
                </div>
                <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800">
                  <span className="text-slate-400 block">Delivery Preference</span>
                  <span className="text-sm font-semibold text-white mt-1 block">
                    {payload.delivery_preference || 'Standard Postal'}
                  </span>
                </div>
                <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800 sm:col-span-1">
                  <span className="text-slate-400 block">Customer Remarks</span>
                  <span className="text-xs text-slate-300 mt-1 block italic">
                    {payload.remarks || 'None specified'}
                  </span>
                </div>
              </div>
            )}

            {request.service_type === 'DEBIT_CARD_REPLACEMENT' && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800">
                  <span className="text-slate-400 block">Replacement Reason</span>
                  <span className="text-sm font-bold text-rose-400 mt-1 block">
                    {payload.replacement_reason || 'Damaged Card'}
                  </span>
                </div>
                <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800">
                  <span className="text-slate-400 block">Customer Notes</span>
                  <span className="text-xs text-slate-300 mt-1 block italic">
                    {payload.remarks || 'None provided'}
                  </span>
                </div>
              </div>
            )}

            {request.service_type === 'ADDRESS_UPDATE' && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800 sm:col-span-2">
                  <span className="text-slate-400 block">New Synthetic Address</span>
                  <span className="text-sm font-semibold text-white mt-1 block">
                    {payload.new_synthetic_address || 'Address on file'}
                  </span>
                  <span className="text-xs text-slate-400 mt-0.5 block">
                    {payload.city}, {payload.state} {payload.postal_code}
                  </span>
                </div>
                <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800">
                  <span className="text-slate-400 block">Reason for Update</span>
                  <span className="text-xs text-slate-300 mt-1 block">
                    {payload.reason_for_update || 'Relocation'}
                  </span>
                </div>
              </div>
            )}

            {request.service_type === 'ACCOUNT_APPLICATION' && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800">
                  <span className="text-slate-400 block">Applicant Name</span>
                  <span className="text-sm font-semibold text-white mt-1 block">
                    {payload.applicant_name || request.customer_name}
                  </span>
                </div>
                <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800">
                  <span className="text-slate-400 block">Requested Account Type</span>
                  <span className="text-sm font-bold text-emerald-400 mt-1 block">
                    {payload.requested_account_type || 'SAVINGS'}
                  </span>
                </div>
                <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800">
                  <span className="text-slate-400 block">Branch Preference</span>
                  <span className="text-xs text-slate-300 mt-1 block">
                    {payload.branch_preference || 'Digital Branch'}
                  </span>
                </div>
                <div className="p-3 bg-amber-950/30 border border-amber-800/60 rounded-lg sm:col-span-3 text-[11px] text-amber-300 flex items-center space-x-2">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                  <span>
                    Notice: Account applications are pre-screening simulations. Review completion records staff concurrence but does not open real regulated accounts.
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Review History */}
          {request.reviews && request.reviews.length > 0 && (
            <div className="bg-[#0f1a3a] border border-slate-800 rounded-xl p-5 space-y-3">
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Supervisory Review History</h4>
              <div className="space-y-2">
                {request.reviews.map((rev) => (
                  <div key={rev.id} className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-emerald-400">{rev.review_decision}</span>
                      <span className="text-slate-400">{new Date(rev.created_at).toLocaleString()}</span>
                    </div>
                    <p className="text-slate-200">{rev.internal_note}</p>
                    <span className="text-[10px] text-slate-500 block">
                      Reviewer: {rev.employee_name || 'Staff Officer'} ({rev.employee_code || 'EMP'})
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Correction History */}
          {request.corrections && request.corrections.length > 0 && (
            <div className="bg-[#0f1a3a] border border-slate-800 rounded-xl p-5 space-y-3">
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Correction Requests Issued</h4>
              <div className="space-y-2">
                {request.corrections.map((corr) => (
                  <div key={corr.id} className="p-3 bg-orange-950/20 border border-orange-800/40 rounded-lg text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-orange-400">{corr.correction_reason}</span>
                      <span className="text-slate-400">{new Date(corr.created_at).toLocaleString()}</span>
                    </div>
                    <p className="text-slate-200">{corr.customer_instruction}</p>
                    <span className="text-[10px] text-slate-500 block">
                      Issued by: {corr.employee_name || 'Officer'} ({corr.employee_code || 'EMP'})
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Action Footer */}
        <div className="p-5 border-t border-slate-800 bg-[#0d1733] flex flex-wrap items-center justify-between gap-3">
          <div className="text-xs text-slate-400">
            Audit ID: <span className="font-mono text-slate-300">{request.request_id}</span>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => onOpenCorrection(request)}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-orange-300 bg-orange-950/40 hover:bg-orange-900/60 border border-orange-700/60 transition flex items-center space-x-1.5"
            >
              <AlertTriangle className="w-4 h-4" />
              <span>Request Correction</span>
            </button>

            <button
              onClick={() => onOpenReview(request)}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-950 bg-emerald-400 hover:bg-emerald-300 transition flex items-center space-x-1.5 shadow-lg shadow-emerald-500/20"
            >
              <ShieldAlert className="w-4 h-4" />
              <span>Record Review Decision</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
