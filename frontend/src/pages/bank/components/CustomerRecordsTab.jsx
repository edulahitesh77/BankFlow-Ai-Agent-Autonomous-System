import React, { useState, useEffect } from 'react';
import {
  Users,
  Search,
  Building,
  CreditCard,
  FileText,
  ChevronLeft,
  ChevronRight,
  X,
  Phone,
  Mail,
  Calendar,
} from 'lucide-react';
import { fetchBankCustomers, fetchBankCustomerDetails } from '../../../api/auth';

export const CustomerRecordsTab = ({ onSelectRequest }) => {
  const [customers, setCustomers] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [branch, setBranch] = useState('ALL');

  // Customer inspection drawer/modal
  const [selectedCustomerId, setSelectedCustomerId] = useState(null);
  const [customerDetail, setCustomerDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const loadData = async (currentPage = page) => {
    setLoading(true);
    try {
      const data = await fetchBankCustomers({ search, branch, page: currentPage, page_size: 10 });
      setCustomers(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
      setPage(data.page);
    } catch (err) {
      console.error('Failed to load customers:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(1);
  }, [branch]);

  const handleOpenCustomer = async (id) => {
    setSelectedCustomerId(id);
    setDetailLoading(true);
    try {
      const detail = await fetchBankCustomerDetails(id);
      setCustomerDetail(detail);
    } catch (err) {
      console.error('Failed to load customer detail:', err);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCloseCustomer = () => {
    setSelectedCustomerId(null);
    setCustomerDetail(null);
  };

  return (
    <div className="space-y-6">
      {/* Search Header */}
      <div className="bg-[#0b132b] border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-purple-400 font-bold text-xs uppercase tracking-wider mb-1">
            <Users className="w-4 h-4" />
            <span>Retail Banking Directory</span>
          </div>
          <h2 className="text-xl font-bold text-white">Registered Customer Profiles</h2>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Inspect synthetic customer KYC records, associated test accounts, and service request history.
            Authentication secrets and credentials are strictly protected.
          </p>
        </div>

        <div className="flex items-center space-x-3 w-full md:w-auto">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              loadData(1);
            }}
            className="relative flex-1 md:w-64"
          >
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search code, name, email..."
              className="w-full pl-9 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-500"
            />
          </form>

          <select
            value={branch}
            onChange={(e) => setBranch(e.target.value)}
            className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-purple-500"
          >
            <option value="ALL">All Branches</option>
            <option value="BR-MAIN-001">Main Branch</option>
            <option value="BR-DIGITAL-001">Digital Branch</option>
            <option value="BR-NORTH-002">North Branch</option>
          </select>
        </div>
      </div>

      {/* Customer Directory Table */}
      <div className="bg-[#0b132b] border border-slate-800 rounded-2xl shadow-xl overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400 flex flex-col items-center space-y-3">
            <div className="w-8 h-8 border-3 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-xs">Loading customer directory...</span>
          </div>
        ) : customers.length === 0 ? (
          <div className="p-12 text-center space-y-2">
            <Users className="w-10 h-10 text-slate-600 mx-auto" />
            <h4 className="text-sm font-semibold text-slate-300">No customers found</h4>
            <p className="text-xs text-slate-500">Try adjusting your search query or branch filter.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-[#0d1733] text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                  <th className="py-3.5 px-4">Customer Code</th>
                  <th className="py-3.5 px-4">Full Name</th>
                  <th className="py-3.5 px-4">Email Address</th>
                  <th className="py-3.5 px-4">Phone</th>
                  <th className="py-3.5 px-4">Branch</th>
                  <th className="py-3.5 px-4">Accounts</th>
                  <th className="py-3.5 px-4">Requests</th>
                  <th className="py-3.5 px-4 text-right">Profile</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80 text-slate-200">
                {customers.map((c) => (
                  <tr
                    key={c.id}
                    className="hover:bg-slate-900/60 transition cursor-pointer"
                    onClick={() => handleOpenCustomer(c.id)}
                  >
                    <td className="py-3.5 px-4 font-mono font-bold text-purple-400">{c.customer_code}</td>
                    <td className="py-3.5 px-4 font-semibold text-white">{c.full_name}</td>
                    <td className="py-3.5 px-4 text-slate-300">{c.email}</td>
                    <td className="py-3.5 px-4 text-slate-400">{c.phone || 'N/A'}</td>
                    <td className="py-3.5 px-4 text-slate-300">{c.branch_id || 'Digital'}</td>
                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-800 text-slate-200">
                        {c.total_accounts}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-purple-500/10 text-purple-400 border border-purple-500/30">
                        {c.total_requests}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() => handleOpenCustomer(c.id)}
                        className="px-3 py-1 rounded-lg text-slate-300 hover:text-white bg-slate-900 hover:bg-slate-800 border border-slate-700 transition"
                      >
                        Inspect
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
              <span className="font-bold text-white">{totalPages}</span> ({total} customers)
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

      {/* Customer Detail Drawer Modal */}
      {selectedCustomerId && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0b132b] border border-slate-800 rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl text-slate-100 overflow-hidden">
            <div className="p-5 border-b border-slate-800 bg-[#0d1733] flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
                  <Users className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Customer Record Inspection</h3>
                  <span className="text-xs text-purple-400 font-mono">
                    {customerDetail?.customer_code || 'Loading...'}
                  </span>
                </div>
              </div>
              <button
                onClick={handleCloseCustomer}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-6 text-xs flex-1">
              {detailLoading ? (
                <div className="p-8 text-center text-slate-400">Loading profile data...</div>
              ) : customerDetail ? (
                <>
                  {/* Basic Profile */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-[#0f1a3a] border border-slate-800">
                    <div>
                      <span className="text-slate-400 block">Full Legal Name</span>
                      <span className="font-bold text-white text-sm mt-0.5 block">{customerDetail.full_name}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Email Address</span>
                      <span className="text-slate-200 mt-0.5 block">{customerDetail.email}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Phone</span>
                      <span className="text-slate-200 mt-0.5 block">{customerDetail.phone || 'Not recorded'}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Home Branch</span>
                      <span className="text-slate-200 mt-0.5 block">{customerDetail.branch_id || 'Digital'}</span>
                    </div>
                  </div>

                  {/* Synthetic Accounts List */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-semibold text-cyan-400 uppercase tracking-wider flex items-center space-x-1.5">
                      <CreditCard className="w-4 h-4" />
                      <span>Associated Synthetic Accounts ({customerDetail.accounts?.length || 0})</span>
                    </h4>
                    {customerDetail.accounts && customerDetail.accounts.length > 0 ? (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {customerDetail.accounts.map((acc) => (
                          <div
                            key={acc.id}
                            className="p-3 bg-slate-900/80 border border-slate-800 rounded-xl space-y-1"
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-mono text-cyan-300 font-semibold">{acc.account_number}</span>
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400">
                                {acc.status}
                              </span>
                            </div>
                            <div className="text-[11px] text-slate-400">
                              Type: <span className="text-slate-200 font-medium">{acc.account_type}</span> • Branch: {acc.branch_id || 'Digital'}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="p-4 text-center text-slate-500 bg-slate-900/40 rounded-xl">
                        No synthetic accounts registered yet.
                      </div>
                    )}
                  </div>

                  {/* Customer Requests History */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider flex items-center space-x-1.5">
                      <FileText className="w-4 h-4" />
                      <span>Request History ({customerDetail.requests?.length || 0})</span>
                    </h4>
                    {customerDetail.requests && customerDetail.requests.length > 0 ? (
                      <div className="space-y-2">
                        {customerDetail.requests.map((r) => (
                          <div
                            key={r.id}
                            onClick={() => {
                              handleCloseCustomer();
                              onSelectRequest(r.request_id);
                            }}
                            className="p-3 bg-slate-900/60 hover:bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between cursor-pointer transition"
                          >
                            <div className="space-y-0.5">
                              <span className="font-mono font-bold text-white">{r.request_id}</span>
                              <div className="text-[11px] text-slate-400">
                                {r.service_type.replace(/_/g, ' ')} • Submitted on {new Date(r.created_at).toLocaleDateString()}
                              </div>
                            </div>
                            <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold border bg-slate-800 border-slate-700 text-slate-300">
                              {r.request_status}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="p-4 text-center text-slate-500 bg-slate-900/40 rounded-xl">
                        No service requests submitted yet.
                      </div>
                    )}
                  </div>
                </>
              ) : null}
            </div>

            <div className="p-4 border-t border-slate-800 bg-[#0d1733] flex justify-end">
              <button
                onClick={handleCloseCustomer}
                className="px-4 py-2 rounded-xl text-slate-300 hover:text-white bg-slate-900 hover:bg-slate-800 border border-slate-700 transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
