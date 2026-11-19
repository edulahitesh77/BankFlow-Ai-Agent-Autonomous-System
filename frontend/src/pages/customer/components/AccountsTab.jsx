import React, { useState } from 'react';
import {
  CreditCard,
  PlusCircle,
  ShieldAlert,
  Calendar,
  Building,
  CheckCircle2,
  AlertCircle,
  Copy,
  Check,
} from 'lucide-react';
import { createSyntheticAccount } from '../../../api/auth';

export const AccountsTab = ({ accounts = [], onRefreshAccounts }) => {
  const [creating, setCreating] = useState(false);
  const [accountType, setAccountType] = useState('SAVINGS');
  const [copiedId, setCopiedId] = useState(null);
  const [msg, setMsg] = useState('');
  const [error, setError] = useState('');

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    setMsg('');
    setError('');
    try {
      await createSyntheticAccount({ account_type: accountType, branch_id: 'BR-MAIN-001' });
      setMsg(`New synthetic ${accountType} demo account created successfully!`);
      await onRefreshAccounts();
    } catch (err) {
      setError(err.message || 'Failed to create synthetic account.');
    } finally {
      setCreating(false);
    }
  };

  const handleCopy = (accNum) => {
    navigator.clipboard.writeText(accNum);
    setCopiedId(accNum);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header and Action */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
        <div>
          <h2 className="text-xl font-bold text-slate-900">My Synthetic Accounts</h2>
          <p className="text-xs text-slate-500 mt-1">
            View simulated account details retrieved from the PostgreSQL database
          </p>
        </div>

        <form onSubmit={handleCreate} className="flex items-center space-x-2 w-full sm:w-auto">
          <select
            value={accountType}
            onChange={(e) => setAccountType(e.target.value)}
            className="text-xs font-semibold px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="SAVINGS">Savings Account</option>
            <option value="CHECKING">Checking Account</option>
            <option value="FIXED_DEPOSIT">Fixed Deposit</option>
          </select>
          <button
            type="submit"
            disabled={creating}
            className="inline-flex items-center space-x-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold transition shadow-md shadow-blue-500/20 disabled:opacity-60"
          >
            <PlusCircle className="w-4 h-4" />
            <span>{creating ? 'Generating...' : 'Add Demo Account'}</span>
          </button>
        </form>
      </div>

      {/* Notifications */}
      {msg && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center space-x-3 text-emerald-800 text-xs font-medium">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          <span>{msg}</span>
        </div>
      )}
      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 flex items-center space-x-3 text-red-700 text-xs font-medium">
          <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Security notice regarding fictional financial information */}
      <div className="p-4 bg-blue-50/70 border border-blue-200 rounded-2xl flex items-start space-x-3 text-xs text-blue-900">
        <ShieldAlert className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <strong>Fictional Account Simulation:</strong> These are synthetic educational banking records.
          Real monetary deposits, withdrawals, and financial transactions are strictly disabled in this simulation.
        </div>
      </div>

      {/* Accounts List / Grid */}
      {accounts && accounts.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {accounts.map((acc) => (
            <div
              key={acc.id}
              className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm hover:border-blue-300 hover:shadow-md transition space-y-4 flex flex-col justify-between"
            >
              <div>
                <div className="flex justify-between items-start">
                  <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                      <CreditCard className="w-4 h-4" />
                    </div>
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                      {acc.account_type}
                    </span>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    {acc.account_status}
                  </span>
                </div>

                {/* Account Number Box */}
                <div className="mt-4 p-3.5 bg-slate-50 rounded-2xl border border-slate-100 flex items-center justify-between">
                  <div>
                    <div className="text-[10px] font-bold uppercase text-slate-400">Account Number</div>
                    <div className="font-mono text-sm font-bold text-slate-900 tracking-wider">
                      {acc.synthetic_account_number}
                    </div>
                  </div>
                  <button
                    onClick={() => handleCopy(acc.synthetic_account_number)}
                    className="p-1.5 text-slate-400 hover:text-blue-600 rounded-lg hover:bg-white transition"
                    title="Copy Account Number"
                  >
                    {copiedId === acc.synthetic_account_number ? (
                      <Check className="w-4 h-4 text-emerald-600" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>

              {/* Meta details */}
              <div className="pt-3 border-t border-slate-100 text-xs text-slate-500 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="flex items-center space-x-1">
                    <Building className="w-3.5 h-3.5 text-slate-400" />
                    <span>Branch</span>
                  </span>
                  <span className="font-medium text-slate-700">{acc.branch_id || 'Main Branch'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center space-x-1">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    <span>Opened</span>
                  </span>
                  <span className="font-medium text-slate-700">
                    {new Date(acc.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* Empty State */
        <div className="bg-white rounded-3xl p-12 text-center border border-dashed border-slate-200 shadow-sm space-y-4 max-w-xl mx-auto">
          <div className="w-16 h-16 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mx-auto">
            <CreditCard className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-bold text-slate-900">No Synthetic Accounts Found</h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            You do not have any synthetic banking accounts linked to your profile yet.
            Click below to generate a fictional demo account for testing service requests.
          </p>
          <button
            onClick={handleCreate}
            disabled={creating}
            className="inline-flex items-center space-x-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold shadow-md shadow-blue-500/20 transition disabled:opacity-60"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Generate First Demo Account</span>
          </button>
        </div>
      )}
    </div>
  );
};
