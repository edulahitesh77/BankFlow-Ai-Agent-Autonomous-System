import React, { useState, useEffect } from 'react';
import { ShieldCheck, Search, Filter, RotateCw, ChevronLeft, ChevronRight } from 'lucide-react';
import { fetchBankAuditLogs } from '../../../api/auth';

export const AuditLogsTab = () => {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [actionFilter, setActionFilter] = useState('ALL');
  const [entityTypeFilter, setEntityTypeFilter] = useState('ALL');

  const actionOptions = [
    'ALL',
    'EMPLOYEE_LOGIN',
    'CUSTOMER_LOGIN',
    'CUSTOMER_REGISTERED',
    'SERVICE_REQUEST_SUBMITTED',
    'EMPLOYEE_VIEWED_REQUEST',
    'HUMAN_REVIEW_DECISION',
    'CORRECTION_REQUESTED',
    'CUSTOMER_CORRECTION_SUBMITTED',
    'USER_LOGOUT',
  ];

  const entityTypeOptions = ['ALL', 'REQUEST', 'USER', 'CUSTOMER', 'EMPLOYEE', 'AUTH'];

  const loadData = async (currentPage = page) => {
    setLoading(true);
    try {
      const data = await fetchBankAuditLogs({
        action: actionFilter,
        entity_type: entityTypeFilter,
        search,
        page: currentPage,
        page_size: 15,
      });
      setLogs(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
      setPage(data.page);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(1);
  }, [actionFilter, entityTypeFilter]);

  return (
    <div className="space-y-6">
      {/* Header & Filter Controls */}
      <div className="bg-[#0b132b] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div>
          <div className="flex items-center space-x-2 text-emerald-400 font-bold text-xs uppercase tracking-wider mb-1">
            <ShieldCheck className="w-4 h-4" />
            <span>Compliance & Regulatory Observability</span>
          </div>
          <h2 className="text-xl font-bold text-white">System Compliance Audit Ledger</h2>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Cryptographically sealed, backend-recorded activity log capturing employee decisions, customer submissions,
            and state changes. Front-end submissions cannot tamper with this ledger.
          </p>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              loadData(1);
            }}
            className="relative flex-1 min-w-[240px] max-w-md"
          >
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search description, action, or entity ID..."
              className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
            />
          </form>

          <div className="flex flex-wrap items-center gap-3 text-xs">
            {/* Action Filter */}
            <select
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              {actionOptions.map((act) => (
                <option key={act} value={act}>
                  {act === 'ALL' ? 'All Actions' : act.replace(/_/g, ' ')}
                </option>
              ))}
            </select>

            {/* Entity Type Filter */}
            <select
              value={entityTypeFilter}
              onChange={(e) => setEntityTypeFilter(e.target.value)}
              className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              {entityTypeOptions.map((ent) => (
                <option key={ent} value={ent}>
                  {ent === 'ALL' ? 'All Entities' : ent}
                </option>
              ))}
            </select>

            <button
              onClick={() => loadData(page)}
              className="p-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-xl text-slate-300 hover:text-white transition"
              title="Refresh ledger"
            >
              <RotateCw className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-[#0b132b] border border-slate-800 rounded-2xl shadow-xl overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400 flex flex-col items-center space-y-3">
            <div className="w-8 h-8 border-3 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-xs">Loading compliance audit entries...</span>
          </div>
        ) : logs.length === 0 ? (
          <div className="p-12 text-center space-y-2">
            <ShieldCheck className="w-10 h-10 text-slate-600 mx-auto" />
            <h4 className="text-sm font-semibold text-slate-300">No matching audit events</h4>
            <p className="text-xs text-slate-500">Try adjusting your search criteria or action filter.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-[#0d1733] text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                  <th className="py-3.5 px-4">Timestamp</th>
                  <th className="py-3.5 px-4">Actor</th>
                  <th className="py-3.5 px-4">Role</th>
                  <th className="py-3.5 px-4">Action</th>
                  <th className="py-3.5 px-4">Entity</th>
                  <th className="py-3.5 px-4">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80 text-slate-200 font-mono text-[11px]">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-900/60 transition">
                    <td className="py-3 px-4 text-slate-400 whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-slate-100 font-sans font-medium whitespace-nowrap">
                      {log.actor}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 font-sans">
                        {log.role}
                      </span>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold font-sans border ${
                          log.action.includes('REJECT')
                            ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                            : log.action.includes('CORRECTION')
                            ? 'bg-orange-500/10 text-orange-400 border-orange-500/30'
                            : log.action.includes('REVIEW')
                            ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                            : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                        }`}
                      >
                        {log.action}
                      </span>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap text-slate-300">
                      {log.entity_type} {log.entity_id ? `(${log.entity_id})` : ''}
                    </td>
                    <td className="py-3 px-4 font-sans text-slate-300 max-w-md truncate">
                      {log.description}
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
              <span className="font-bold text-white">{totalPages}</span> ({total} audit events)
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
