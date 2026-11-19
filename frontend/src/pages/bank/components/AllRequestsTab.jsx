import React, { useState, useEffect } from 'react';
import {
  Search,
  Filter,
  Eye,
  ShieldAlert,
  AlertTriangle,
  RotateCw,
  ChevronLeft,
  ChevronRight,
  FileText,
} from 'lucide-react';
import { fetchBankRequests } from '../../../api/auth';

export const AllRequestsTab = ({
  initialStatus = 'ALL',
  onSelectRequest,
  onOpenReview,
  onOpenCorrection,
  onInspectCustomer,
}) => {
  const [requests, setRequests] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Filters
  const [statusFilter, setStatusFilter] = useState(initialStatus);
  const [serviceTypeFilter, setServiceTypeFilter] = useState('ALL');
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [search, setSearch] = useState('');

  const statusOptions = [
    'ALL',
    'NEW',
    'CLASSIFIED',
    'QUEUED',
    'VERIFIED',
    'IN_SERVICE',
    'COMPLETED',
    'NEEDS_CORRECTION',
    'HUMAN_REVIEW',
    'REJECTED_INPUT',
    'FAILED',
  ];

  const serviceTypeOptions = [
    { key: 'ALL', label: 'All Services' },
    { key: 'CHEQUE_BOOK', label: 'Cheque Book' },
    { key: 'DEBIT_CARD_REPLACEMENT', label: 'Debit Card Replacement' },
    { key: 'ADDRESS_UPDATE', label: 'Address Update' },
    { key: 'ACCOUNT_APPLICATION', label: 'Account Application' },
  ];

  const loadData = async (currentPage = page) => {
    setLoading(true);
    setError('');
    try {
      const data = await fetchBankRequests({
        status: statusFilter,
        service_type: serviceTypeFilter,
        priority: priorityFilter,
        search,
        page: currentPage,
        page_size: 10,
      });
      setRequests(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
      setPage(data.page);
    } catch (err) {
      setError(err.message || 'Failed to load requests.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(1);
  }, [statusFilter, serviceTypeFilter, priorityFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadData(1);
  };

  return (
    <div className="space-y-6">
      {/* Top Controls: Search & Filters */}
      <div className="bg-[#0b132b] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <form onSubmit={handleSearchSubmit} className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by Request ID, Customer Code, or Name..."
              className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
            />
          </form>

          <div className="flex flex-wrap items-center gap-3 text-xs">
            {/* Service Type Filter */}
            <select
              value={serviceTypeFilter}
              onChange={(e) => setServiceTypeFilter(e.target.value)}
              className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              {serviceTypeOptions.map((opt) => (
                <option key={opt.key} value={opt.key}>
                  {opt.label}
                </option>
              ))}
            </select>

            {/* Priority Filter */}
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="ALL">All Priorities</option>
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
              <option value="URGENT">Urgent</option>
            </select>

            <button
              onClick={() => loadData(page)}
              className="p-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-xl text-slate-300 hover:text-white transition"
              title="Refresh requests"
            >
              <RotateCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Status Filter Horizontal Pills */}
        <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 text-xs no-scrollbar">
          {statusOptions.map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition ${
                statusFilter === st
                  ? 'bg-emerald-500 text-slate-950 font-bold shadow-md shadow-emerald-500/20'
                  : 'bg-slate-900/80 text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              {st.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Table Container */}
      <div className="bg-[#0b132b] border border-slate-800 rounded-2xl shadow-xl overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400 flex flex-col items-center space-y-3">
            <div className="w-8 h-8 border-3 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-xs">Loading banking requests...</span>
          </div>
        ) : error ? (
          <div className="p-8 text-center text-red-400 text-xs">
            {error}
          </div>
        ) : requests.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <FileText className="w-10 h-10 text-slate-600 mx-auto" />
            <h4 className="text-sm font-semibold text-slate-300">No requests match your criteria</h4>
            <p className="text-xs text-slate-500">Try adjusting your filters or search terms.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-[#0d1733] text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                  <th className="py-3.5 px-4">Request ID</th>
                  <th className="py-3.5 px-4">Customer</th>
                  <th className="py-3.5 px-4">Service Type</th>
                  <th className="py-3.5 px-4">Submitted</th>
                  <th className="py-3.5 px-4">Priority</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Agent</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80 text-slate-200">
                {requests.map((req) => (
                  <tr
                    key={req.id}
                    className="hover:bg-slate-900/60 transition group cursor-pointer"
                    onClick={() => onSelectRequest(req.request_id)}
                  >
                    <td className="py-3.5 px-4 font-mono font-bold text-white whitespace-nowrap">
                      {req.request_id}
                    </td>

                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <div className="font-semibold text-slate-100">{req.customer_name}</div>
                      <div className="text-[11px] font-mono text-emerald-400">{req.customer_code}</div>
                    </td>

                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <span className="font-medium text-slate-200">
                        {req.service_type.replace(/_/g, ' ')}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 whitespace-nowrap text-slate-400 font-mono">
                      {new Date(req.created_at).toLocaleDateString()}
                    </td>

                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          req.priority === 'HIGH' || req.priority === 'URGENT'
                            ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                            : 'bg-slate-800 text-slate-300'
                        }`}
                      >
                        {req.priority}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <span
                        className={`px-2.5 py-1 rounded-full text-[11px] font-semibold border ${
                          req.request_status === 'COMPLETED'
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                            : req.request_status === 'HUMAN_REVIEW'
                            ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                            : req.request_status === 'NEEDS_CORRECTION'
                            ? 'bg-orange-500/10 text-orange-400 border-orange-500/30'
                            : req.request_status === 'REJECTED_INPUT' || req.request_status === 'FAILED'
                            ? 'bg-red-500/10 text-red-400 border-red-500/30'
                            : 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30'
                        }`}
                      >
                        {req.request_status.replace(/_/g, ' ')}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 whitespace-nowrap text-slate-400 font-mono">
                      {req.assigned_agent_code || 'Pending'}
                    </td>

                    <td
                      className="py-3.5 px-4 whitespace-nowrap text-right space-x-2"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <button
                        onClick={() => onSelectRequest(req.request_id)}
                        className="px-2.5 py-1 rounded-lg text-slate-300 hover:text-white bg-slate-900 hover:bg-slate-800 border border-slate-700 transition"
                        title="View Full Details"
                      >
                        Inspect
                      </button>
                      <button
                        onClick={() => onOpenReview(req)}
                        className="px-2.5 py-1 rounded-lg text-emerald-400 hover:text-emerald-300 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 transition"
                        title="Record Review Decision"
                      >
                        Review
                      </button>
                      <button
                        onClick={() => onOpenCorrection(req)}
                        className="px-2.5 py-1 rounded-lg text-orange-400 hover:text-orange-300 bg-orange-500/10 hover:bg-orange-500/20 border border-orange-500/30 transition"
                        title="Request Customer Correction"
                      >
                        Correct
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        {!loading && totalPages > 1 && (
          <div className="p-4 border-t border-slate-800 bg-[#0d1733] flex items-center justify-between text-xs text-slate-400">
            <div>
              Showing page <span className="font-bold text-white">{page}</span> of{' '}
              <span className="font-bold text-white">{totalPages}</span> ({total} requests)
            </div>
            <div className="flex items-center space-x-2">
              <button
                disabled={page <= 1}
                onClick={() => loadData(page - 1)}
                className="p-1.5 rounded-lg bg-slate-900 border border-slate-700 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-800 text-slate-300"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => loadData(page + 1)}
                className="p-1.5 rounded-lg bg-slate-900 border border-slate-700 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-800 text-slate-300"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
