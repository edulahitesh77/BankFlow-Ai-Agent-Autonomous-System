import React, { useState, useEffect } from 'react';
import { XCircle, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { fetchRejectedRequests } from '../../../api/auth';

export const RejectedRequestsTab = ({ onSelectRequest }) => {
  const [requests, setRequests] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const loadData = async (currentPage = page) => {
    setLoading(true);
    try {
      const data = await fetchRejectedRequests({ search, page: currentPage, page_size: 10 });
      setRequests(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
      setPage(data.page);
    } catch (err) {
      console.error('Failed to load rejected requests:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(1);
  }, []);

  return (
    <div className="space-y-6">
      <div className="bg-[#0b132b] border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-rose-400 font-bold text-xs uppercase tracking-wider mb-1">
            <XCircle className="w-4 h-4" />
            <span>Audited Rejection Archive</span>
          </div>
          <h2 className="text-xl font-bold text-white">Rejected Customer Banking Requests</h2>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Immutable log of requests terminated due to compliance failure, fraud thresholds, or customer non-responsiveness.
            Rejections cannot be silently converted to approved requests.
          </p>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            loadData(1);
          }}
          className="relative max-w-xs w-full"
        >
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search request or customer..."
            className="w-full pl-9 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-rose-500"
          />
        </form>
      </div>

      <div className="bg-[#0b132b] border border-slate-800 rounded-2xl shadow-xl overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400 flex flex-col items-center space-y-3">
            <div className="w-8 h-8 border-3 border-rose-500 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-xs">Loading rejected requests...</span>
          </div>
        ) : requests.length === 0 ? (
          <div className="p-12 text-center space-y-2">
            <XCircle className="w-10 h-10 text-slate-600 mx-auto" />
            <h4 className="text-sm font-semibold text-slate-300">No Rejected Requests</h4>
            <p className="text-xs text-slate-500">There are no rejected service requests recorded.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-[#0d1733] text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                  <th className="py-3.5 px-4">Request ID</th>
                  <th className="py-3.5 px-4">Customer</th>
                  <th className="py-3.5 px-4">Service Type</th>
                  <th className="py-3.5 px-4">Rejection Reason Code</th>
                  <th className="py-3.5 px-4">Terminated Date</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80 text-slate-200">
                {requests.map((req) => (
                  <tr
                    key={req.id}
                    className="hover:bg-slate-900/60 transition cursor-pointer"
                    onClick={() => onSelectRequest(req.request_id)}
                  >
                    <td className="py-3.5 px-4 font-mono font-bold text-white">{req.request_id}</td>
                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-slate-100">{req.customer_name}</div>
                      <div className="text-[11px] font-mono text-rose-400">{req.customer_code}</div>
                    </td>
                    <td className="py-3.5 px-4 font-medium">{req.service_type.replace(/_/g, ' ')}</td>
                    <td className="py-3.5 px-4 text-rose-300 font-medium">
                      {req.reason_code || 'HUMAN_REVIEW_REJECTED'}
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 font-mono">
                      {new Date(req.updated_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() => onSelectRequest(req.request_id)}
                        className="px-3 py-1 rounded-lg text-slate-300 hover:text-white bg-slate-900 hover:bg-slate-800 border border-slate-700 transition"
                      >
                        Inspect Audit Trail
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
              Page <span className="font-bold text-white">{page}</span> of{' '}
              <span className="font-bold text-white">{totalPages}</span>
            </div>
            <div className="flex items-center space-x-2">
              <button
                disabled={page <= 1}
                onClick={() => loadData(page - 1)}
                className="p-1.5 rounded-lg bg-slate-900 border border-slate-700 disabled:opacity-40"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => loadData(page + 1)}
                className="p-1.5 rounded-lg bg-slate-900 border border-slate-700 disabled:opacity-40"
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
