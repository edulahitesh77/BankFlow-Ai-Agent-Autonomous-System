import React from 'react';
import {
  CreditCard,
  FileText,
  Clock,
  CheckCircle2,
  PlusCircle,
  Search,
  ArrowRight,
  ShieldCheck,
  AlertCircle,
} from 'lucide-react';

export const getStatusBadge = (status) => {
  const map = {
    NEW: 'bg-blue-100 text-blue-800 border-blue-200',
    CLASSIFIED: 'bg-cyan-100 text-cyan-800 border-cyan-200',
    QUEUED: 'bg-indigo-100 text-indigo-800 border-indigo-200',
    VERIFIED: 'bg-purple-100 text-purple-800 border-purple-200',
    IN_SERVICE: 'bg-amber-100 text-amber-800 border-amber-200',
    COMPLETED: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    NEEDS_CORRECTION: 'bg-orange-100 text-orange-800 border-orange-200 animate-pulse',
    HUMAN_REVIEW: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    REJECTED_INPUT: 'bg-rose-100 text-rose-800 border-rose-200',
    FAILED: 'bg-red-100 text-red-800 border-red-200',
  };
  return map[status] || 'bg-slate-100 text-slate-800 border-slate-200';
};

export const DashboardOverview = ({ dashboardData, onNavigateTab, onSelectRequest }) => {
  const summary = dashboardData?.summary || {
    total_accounts: 0,
    total_requests: 0,
    pending_requests: 0,
    completed_requests: 0,
  };

  const recent = dashboardData?.recent_requests || [];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-blue-700 via-blue-600 to-indigo-700 rounded-3xl p-6 sm:p-8 text-white shadow-xl shadow-blue-900/10 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div className="space-y-2">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-white/10 text-xs font-semibold backdrop-blur-sm">
            <ShieldCheck className="w-3.5 h-3.5 text-blue-200" />
            <span>Authenticated Banking Session • Customer Portal</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Welcome back, {dashboardData?.customer_name}!
          </h1>
          <p className="text-blue-100 text-xs sm:text-sm max-w-xl">
            Manage your synthetic accounts, track automated multi-agent service workflows, and submit new requests.
          </p>
        </div>

        <div className="bg-white/10 backdrop-blur-md px-5 py-4 rounded-2xl border border-white/20 text-xs space-y-1 w-full md:w-auto">
          <div className="text-blue-200 font-medium">Customer Code</div>
          <div className="text-lg font-mono font-bold">{dashboardData?.customer_code}</div>
          <div className="text-blue-200">Branch: {dashboardData?.branch}</div>
        </div>
      </div>

      {/* Top Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Total Accounts */}
        <div
          onClick={() => onNavigateTab('accounts')}
          className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:border-blue-300 hover:shadow-md transition cursor-pointer group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Total Accounts</span>
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center group-hover:scale-110 transition">
              <CreditCard className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 text-3xl font-extrabold text-slate-900">{summary.total_accounts}</div>
          <div className="mt-1 text-xs text-slate-500 flex items-center space-x-1">
            <span>Synthetic banking profiles</span>
          </div>
        </div>

        {/* Total Requests */}
        <div
          onClick={() => onNavigateTab('my_requests')}
          className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:border-blue-300 hover:shadow-md transition cursor-pointer group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Total Requests</span>
            <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center group-hover:scale-110 transition">
              <FileText className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 text-3xl font-extrabold text-slate-900">{summary.total_requests}</div>
          <div className="mt-1 text-xs text-slate-500">All submitted service tickets</div>
        </div>

        {/* Pending Requests */}
        <div
          onClick={() => onNavigateTab('my_requests')}
          className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:border-amber-300 hover:shadow-md transition cursor-pointer group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Pending Requests</span>
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center group-hover:scale-110 transition">
              <Clock className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 text-3xl font-extrabold text-amber-600">{summary.pending_requests}</div>
          <div className="mt-1 text-xs text-slate-500">In workflow or awaiting intake</div>
        </div>

        {/* Completed Requests */}
        <div
          onClick={() => onNavigateTab('my_requests')}
          className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:border-emerald-300 hover:shadow-md transition cursor-pointer group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Completed Requests</span>
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center group-hover:scale-110 transition">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 text-3xl font-extrabold text-emerald-600">{summary.completed_requests}</div>
          <div className="mt-1 text-xs text-slate-500">Finalized / processed</div>
        </div>
      </div>

      {/* Quick Action Shortcuts */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button
          onClick={() => onNavigateTab('new_request')}
          className="flex items-center justify-between p-4 bg-blue-50/70 hover:bg-blue-100/70 border border-blue-200 rounded-2xl text-left transition group"
        >
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-sm">
              <PlusCircle className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-bold text-blue-950">New Service Request</div>
              <div className="text-xs text-blue-700">Cheque book, card, address, or application</div>
            </div>
          </div>
          <ArrowRight className="w-4 h-4 text-blue-600 group-hover:translate-x-1 transition" />
        </button>

        <button
          onClick={() => onNavigateTab('track_request')}
          className="flex items-center justify-between p-4 bg-indigo-50/70 hover:bg-indigo-100/70 border border-indigo-200 rounded-2xl text-left transition group"
        >
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-600 text-white flex items-center justify-center shadow-sm">
              <Search className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-bold text-indigo-950">Track Service Request</div>
              <div className="text-xs text-indigo-700">Check stage & multi-agent status</div>
            </div>
          </div>
          <ArrowRight className="w-4 h-4 text-indigo-600 group-hover:translate-x-1 transition" />
        </button>

        <button
          onClick={() => onNavigateTab('accounts')}
          className="flex items-center justify-between p-4 bg-slate-100/80 hover:bg-slate-200/80 border border-slate-200 rounded-2xl text-left transition group"
        >
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-slate-800 text-white flex items-center justify-center shadow-sm">
              <CreditCard className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-bold text-slate-900">View My Accounts</div>
              <div className="text-xs text-slate-600">Synthetic account numbers & details</div>
            </div>
          </div>
          <ArrowRight className="w-4 h-4 text-slate-700 group-hover:translate-x-1 transition" />
        </button>
      </div>

      {/* Recent Requests Table */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-sm space-y-5">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div>
            <h3 className="text-lg font-bold text-slate-900">Recent Service Requests</h3>
            <p className="text-xs text-slate-500">Live request status retrieved from database</p>
          </div>
          <button
            onClick={() => onNavigateTab('my_requests')}
            className="text-xs font-semibold text-blue-600 hover:text-blue-800 inline-flex items-center space-x-1"
          >
            <span>View All Requests</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {recent.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs sm:text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                  <th className="py-3 px-3">Request ID</th>
                  <th className="py-3 px-3">Service Type</th>
                  <th className="py-3 px-3">Submission Date</th>
                  <th className="py-3 px-3">Current Status</th>
                  <th className="py-3 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {recent.map((req) => (
                  <tr key={req.id} className="hover:bg-slate-50/80 transition">
                    <td className="py-3.5 px-3 font-mono font-bold text-slate-900">
                      {req.request_id}
                    </td>
                    <td className="py-3.5 px-3 font-medium text-slate-700">
                      {req.service_type.replace(/_/g, ' ')}
                    </td>
                    <td className="py-3.5 px-3 text-slate-500">
                      {new Date(req.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-3">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${getStatusBadge(req.request_status)}`}>
                        {req.request_status}
                      </span>
                    </td>
                    <td className="py-3.5 px-3 text-right">
                      <button
                        onClick={() => {
                          onSelectRequest(req.request_id);
                          onNavigateTab('track_request');
                        }}
                        className="px-3 py-1.5 bg-blue-50 text-blue-600 hover:bg-blue-100 font-semibold rounded-lg text-xs transition"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-12 text-center space-y-3">
            <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center mx-auto">
              <FileText className="w-6 h-6" />
            </div>
            <h4 className="text-sm font-bold text-slate-800">No Service Requests Submitted Yet</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Get started by submitting a Cheque Book, Debit Card, or Address Update request.
            </p>
            <button
              onClick={() => onNavigateTab('new_request')}
              className="mt-2 inline-flex items-center space-x-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold shadow-sm transition"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Create First Request</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
