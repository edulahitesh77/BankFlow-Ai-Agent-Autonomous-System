import React, { useState, useEffect } from 'react';
import {
  Network,
  Building2,
  ShieldCheck,
  ShieldAlert,
  Activity,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Send,
  Database,
  ArrowRight,
  Lock,
  AlertTriangle,
} from 'lucide-react';
import {
  fetchFederatedBranches,
  fetchFederationStatistics,
  fetchFederationEvents,
  triggerCrossBranchExchange,
} from '../../../api/auth';

export const BranchFederationTab = () => {
  const [branches, setBranches] = useState([]);
  const [stats, setStats] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Interactive exchange simulation state
  const [sourceBranch, setSourceBranch] = useState('BLR001');
  const [destBranch, setDestBranch] = useState('CHE001');
  const [scope, setScope] = useState('ACCOUNT_STATUS_CONFIRMATION');
  const [targetAccount, setTargetAccount] = useState('ACC-CHE001-1001');
  const [submitting, setSubmitting] = useState(false);
  const [simResult, setSimResult] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError('');
      const [branchesData, statsData, eventsData] = await Promise.all([
        fetchFederatedBranches(),
        fetchFederationStatistics(),
        fetchFederationEvents({ limit: 20 }),
      ]);
      setBranches(branchesData);
      setStats(statsData);
      setEvents(eventsData);
    } catch (err) {
      setError(err.message || 'Failed to load federation data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSimulateExchange = async (e) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      setSimResult(null);
      const payload = {
        source_branch_id: sourceBranch,
        destination_branch_id: destBranch,
        requested_scope: scope,
        request_id: `SIM-REQ-${Date.now().toString().slice(-6)}`,
        correlation_id: `corr-sim-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`,
        query_params: {
          synthetic_account_number: targetAccount,
          customer_code: `CUST-${destBranch}-0001`,
          service_type: 'CHEQUE_BOOK',
        },
      };

      const result = await triggerCrossBranchExchange(payload);
      setSimResult(result);
      await loadData();
    } catch (err) {
      setSimResult({
        status: 'ERROR',
        error_message: err.message,
        authorization_result: 'REQUEST_ERROR',
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900/60 p-6 rounded-2xl border border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Network className="w-6 h-6 text-indigo-400" />
            <h2 className="text-xl font-bold text-white">Branch Federation Monitoring</h2>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Simulated multi-branch banking federation across Bengaluru (BLR001), Chennai (CHE001), and Hyderabad (HYD001) with controlled Federation Gateway.
          </p>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-sm font-medium border border-slate-700 transition"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh Federation
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-950/40 border border-red-800/60 rounded-xl text-red-300 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-slate-900/40 border border-slate-800/80 p-4 rounded-xl">
          <div className="text-xs text-slate-400 font-medium">Total Branches</div>
          <div className="text-2xl font-bold text-white mt-1">{stats?.total_branches ?? 3}</div>
          <div className="text-xs text-indigo-400 mt-1">Federated Swarms</div>
        </div>
        <div className="bg-slate-900/40 border border-slate-800/80 p-4 rounded-xl">
          <div className="text-xs text-slate-400 font-medium">Active Branches</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{stats?.active_branches ?? 3}</div>
          <div className="text-xs text-emerald-500 mt-1">100% Operational</div>
        </div>
        <div className="bg-slate-900/40 border border-slate-800/80 p-4 rounded-xl">
          <div className="text-xs text-slate-400 font-medium">Total Exchanges</div>
          <div className="text-2xl font-bold text-blue-400 mt-1">{stats?.total_exchanges ?? 0}</div>
          <div className="text-xs text-slate-400 mt-1">Gateway Operations</div>
        </div>
        <div className="bg-slate-900/40 border border-slate-800/80 p-4 rounded-xl">
          <div className="text-xs text-slate-400 font-medium">Successful</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{stats?.successful_exchanges ?? 0}</div>
          <div className="text-xs text-slate-400 mt-1">Authorized Returns</div>
        </div>
        <div className="bg-slate-900/40 border border-slate-800/80 p-4 rounded-xl">
          <div className="text-xs text-slate-400 font-medium">Rejected</div>
          <div className="text-2xl font-bold text-amber-400 mt-1">{stats?.rejected_exchanges ?? 0}</div>
          <div className="text-xs text-slate-400 mt-1">Policy Rejections</div>
        </div>
        <div className="bg-slate-900/40 border border-slate-800/80 p-4 rounded-xl">
          <div className="text-xs text-slate-400 font-medium">Gateway Status</div>
          <div className="text-sm font-bold text-emerald-400 mt-2 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            PROTECTED
          </div>
          <div className="text-xs text-slate-400 mt-1">HMAC & Anti-Replay</div>
        </div>
      </div>

      {/* 3 Independent Branches Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {branches.map((b) => (
          <div
            key={b.branch_id}
            className="bg-slate-900/50 border border-slate-800 p-5 rounded-2xl relative overflow-hidden hover:border-slate-700 transition"
          >
            <div className="flex justify-between items-start">
              <div>
                <span className="text-xs font-mono text-indigo-400 font-semibold px-2 py-0.5 rounded bg-indigo-950/60 border border-indigo-800/50">
                  {b.branch_id}
                </span>
                <h3 className="text-lg font-bold text-white mt-2">{b.branch_name} Branch</h3>
                <p className="text-xs text-slate-400">{b.location}</p>
              </div>
              <span
                className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
                  b.branch_status === 'ACTIVE'
                    ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/60'
                    : 'bg-red-950/80 text-red-400 border border-red-800/60'
                }`}
              >
                {b.branch_status}
              </span>
            </div>

            <div className="mt-4 pt-4 border-t border-slate-800/80 space-y-2 text-xs">
              <div className="flex justify-between text-slate-400">
                <span className="flex items-center gap-1.5">
                  <Database className="w-3.5 h-3.5 text-slate-500" />
                  Database
                </span>
                <span className="font-mono text-slate-300">bankflow_ai_{b.branch_id.slice(0, 3).toLowerCase()}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span className="flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-cyan-400" />
                  Active Agents
                </span>
                <span className="font-semibold text-slate-200">{b.active_agents} agents</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Pending Requests</span>
                <span className="text-amber-400 font-semibold">{b.pending_requests}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Completed Requests</span>
                <span className="text-emerald-400 font-semibold">{b.completed_requests}</span>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-800/50 flex items-center justify-between text-xs text-slate-400">
              <span className="flex items-center gap-1 text-emerald-400">
                <ShieldCheck className="w-3.5 h-3.5" />
                Gateway Linked
              </span>
              <span className="text-slate-500">Isolated DB</span>
            </div>
          </div>
        ))}
      </div>

      {/* Interactive Simulation & Gateway Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Simulation Trigger */}
        <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-2xl">
          <div className="flex items-center gap-2 mb-4">
            <Send className="w-5 h-5 text-indigo-400" />
            <h3 className="text-base font-bold text-white">Simulate Cross-Branch Exchange</h3>
          </div>
          <p className="text-xs text-slate-400 mb-4">
            Trigger an authenticated cross-branch request to test the Federation Gateway authorization and data sanitization layer.
          </p>

          <form onSubmit={handleSimulateExchange} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Source Branch</label>
                <select
                  value={sourceBranch}
                  onChange={(e) => setSourceBranch(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="BLR001">BLR001 (Bengaluru)</option>
                  <option value="CHE001">CHE001 (Chennai)</option>
                  <option value="HYD001">HYD001 (Hyderabad)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Destination Branch</label>
                <select
                  value={destBranch}
                  onChange={(e) => setDestBranch(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="CHE001">CHE001 (Chennai)</option>
                  <option value="HYD001">HYD001 (Hyderabad)</option>
                  <option value="BLR001">BLR001 (Bengaluru)</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Requested Scope</label>
              <select
                value={scope}
                onChange={(e) => setScope(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="ACCOUNT_STATUS_CONFIRMATION">ACCOUNT_STATUS_CONFIRMATION (Authorized)</option>
                <option value="CUSTOMER_KYC_VERIFICATION">CUSTOMER_KYC_VERIFICATION (Authorized)</option>
                <option value="SERVICE_ELIGIBILITY_CONFIRMATION">SERVICE_ELIGIBILITY_CONFIRMATION (Authorized)</option>
                <option value="FULL_ACCOUNT_EXTRACT">FULL_ACCOUNT_EXTRACT (Unauthorized Scope - Rejection Test)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Target Account Number</label>
              <input
                type="text"
                value={targetAccount}
                onChange={(e) => setTargetAccount(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-indigo-500"
                placeholder="e.g. ACC-CHE001-1001"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold py-2.5 rounded-xl text-xs transition"
            >
              {submitting ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  Routing Through Gateway...
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  Execute Authorized Exchange
                </>
              )}
            </button>
          </form>

          {/* Result Card */}
          {simResult && (
            <div className={`mt-4 p-4 rounded-xl border text-xs ${
              simResult.status === 'SUCCESS'
                ? 'bg-emerald-950/40 border-emerald-800/80 text-emerald-200'
                : simResult.status === 'DUPLICATE'
                ? 'bg-amber-950/40 border-amber-800/80 text-amber-200'
                : 'bg-red-950/40 border-red-800/80 text-red-200'
            }`}>
              <div className="flex items-center justify-between font-bold mb-1">
                <span className="flex items-center gap-1.5">
                  {simResult.status === 'SUCCESS' ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-400" />
                  )}
                  Result: {simResult.status} ({simResult.authorization_result})
                </span>
                <span className="font-mono text-slate-400">{simResult.federation_event_id}</span>
              </div>
              {simResult.error_message && (
                <p className="mt-1 text-red-300">{simResult.error_message}</p>
              )}
              {simResult.data && (
                <div className="mt-2 bg-slate-950/80 p-2.5 rounded-lg border border-slate-800/60 font-mono text-[11px] text-slate-300">
                  <pre>{JSON.stringify(simResult.data, null, 2)}</pre>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Security & Architecture Highlights */}
        <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-2xl flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Lock className="w-5 h-5 text-emerald-400" />
              <h3 className="text-base font-bold text-white">Federation Gateway Security Architecture</h3>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed mb-4">
              Cross-branch queries never expose direct database ports or transfer complete customer records. The gateway strictly validates source identity and returns only authorized synthetic confirmations.
            </p>

            <div className="space-y-3 text-xs">
              <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80 flex items-start gap-3">
                <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-white">Branch Identity Authentication</div>
                  <div className="text-slate-400 mt-0.5">
                    HMAC SHA-256 service tokens verified in constant time. Invalid branch keys trigger immediate security rejections.
                  </div>
                </div>
              </div>

              <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80 flex items-start gap-3">
                <ShieldCheck className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-white">Principle of Least Privilege Data Transfer</div>
                  <div className="text-slate-400 mt-0.5">
                    Permitted scopes return only status confirmations (e.g. is_confirmed: true). PII, balances, and passwords are never transferred.
                  </div>
                </div>
              </div>

              <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80 flex items-start gap-3">
                <ShieldCheck className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-white">Anti-Replay & Idempotency</div>
                  <div className="text-slate-400 mt-0.5">
                    Unique correlation IDs detect replay attacks and duplicate submissions, returning cached responses without repeating queries.
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-500 font-mono">
            <span>Gateway: v1.0.0-FED</span>
            <span>Policy: STRICT_LEAST_PRIVILEGE</span>
          </div>
        </div>
      </div>

      {/* Chronological Federation Events Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden">
        <div className="p-5 border-b border-slate-800 flex justify-between items-center">
          <div>
            <h3 className="text-base font-bold text-white">Federation Audit Trail</h3>
            <p className="text-xs text-slate-400 mt-0.5">Immutable event history of inter-branch communications.</p>
          </div>
          <span className="text-xs text-slate-400 font-mono">Total Logged: {events.length}</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 uppercase font-mono text-[10px] border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Event ID</th>
                <th className="py-3 px-4">Routing</th>
                <th className="py-3 px-4">Requested Scope</th>
                <th className="py-3 px-4">Authorization</th>
                <th className="py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {events.length === 0 ? (
                <tr>
                  <td colSpan="6" className="py-8 text-center text-slate-500">
                    No federation events recorded yet. Use the simulation panel above to trigger a cross-branch exchange.
                  </td>
                </tr>
              ) : (
                events.map((ev) => (
                  <tr key={ev.federation_event_id} className="hover:bg-slate-800/30 transition">
                    <td className="py-3 px-4 text-slate-400 whitespace-nowrap">
                      {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : 'N/A'}
                    </td>
                    <td className="py-3 px-4 font-mono text-indigo-300">{ev.federation_event_id}</td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 font-mono">
                        <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-200">{ev.source_branch_id}</span>
                        <ArrowRight className="w-3 h-3 text-slate-500" />
                        <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-200">{ev.destination_branch_id}</span>
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">{ev.requested_scope}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        ev.authorization_result === 'AUTHORIZED'
                          ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/50'
                          : 'bg-red-950/80 text-red-400 border border-red-800/50'
                      }`}>
                        {ev.authorization_result}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        ev.event_status === 'SUCCESS'
                          ? 'bg-emerald-950/80 text-emerald-400'
                          : ev.event_status === 'DUPLICATE'
                          ? 'bg-amber-950/80 text-amber-400'
                          : 'bg-red-950/80 text-red-400'
                      }`}>
                        {ev.event_status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
