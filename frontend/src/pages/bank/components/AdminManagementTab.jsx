import React, { useState, useEffect } from 'react';
import {
  Shield,
  ShieldCheck,
  Lock,
  Users,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Key,
  Server,
  Activity,
  UserCheck,
} from 'lucide-react';
import { fetchAdminUsers, updateUserRole, fetchSecurityStatus } from '../../../api/auth';

export const AdminManagementTab = () => {
  const [users, setUsers] = useState([]);
  const [totalUsers, setTotalUsers] = useState(0);
  const [securityStatus, setSecurityStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [updatingId, setUpdatingId] = useState(null);
  const [message, setMessage] = useState(null);

  const loadData = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);

    try {
      const [uData, sData] = await Promise.all([
        fetchAdminUsers({ page: 1, pageSize: 50 }).catch(() => ({ total: 0, items: [] })),
        fetchSecurityStatus().catch(() => null),
      ]);
      setUsers(uData?.items || []);
      setTotalUsers(uData?.total || 0);
      setSecurityStatus(sData);
    } catch (err) {
      console.error('Failed to load admin data:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRoleChange = async (userId, newRole) => {
    setUpdatingId(userId);
    setMessage(null);
    try {
      const updated = await updateUserRole(userId, newRole);
      setMessage({ type: 'success', text: `Role for ${updated.username} updated to ${updated.role} successfully.` });
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, role: updated.role } : u))
      );
    } catch (err) {
      setMessage({ type: 'error', text: err.message || 'Failed to update user role.' });
    } finally {
      setUpdatingId(null);
    }
  };

  if (loading && !refreshing) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-slate-400">
        <RefreshCw className="w-8 h-8 animate-spin text-emerald-500 mb-2" />
        <p className="text-sm">Loading security architecture and identities...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border border-slate-800 shadow-xl">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-purple-500/10 border border-purple-500/20 rounded-xl text-purple-400">
            <Lock className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-bold text-white tracking-tight">Security Hardening & Access Control</h2>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono bg-purple-500/20 text-purple-300 border border-purple-500/30">
                ADMIN PRIVILEGES
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Role-Based Access Control, AES-256-GCM Key Architecture & Immutable Audit Trail Management
            </p>
          </div>
        </div>

        <button
          onClick={() => loadData(true)}
          disabled={refreshing}
          className="flex items-center px-3.5 py-2 text-xs font-medium text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition-colors shadow-sm disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 mr-2 ${refreshing ? 'animate-spin text-purple-400' : ''}`} />
          {refreshing ? 'Refreshing...' : 'Refresh Status'}
        </button>
      </div>

      {message && (
        <div
          className={`p-4 rounded-xl text-xs font-medium border ${
            message.type === 'success'
              ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
              : 'bg-rose-500/10 text-rose-300 border-rose-500/30'
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Security Architecture Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Password Hashing</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-base font-bold text-white">Argon2id</p>
          <p className="text-[11px] text-slate-500">64MB memory cost, 3 iterations, 16-byte salt</p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Payload Encryption</span>
            <Key className="w-4 h-4 text-purple-400" />
          </div>
          <p className="text-base font-bold text-purple-300">AES-256-GCM</p>
          <p className="text-[11px] text-slate-500">256-bit key, 12-byte random nonces, auth tags</p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Brute-Force Guard</span>
            <ShieldCheck className="w-4 h-4 text-blue-400" />
          </div>
          <p className="text-base font-bold text-blue-400">Rate Limiter Active</p>
          <p className="text-[11px] text-slate-500">5 max attempts / 5 min lockout per identity</p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Audit Security Log</span>
            <Activity className="w-4 h-4 text-amber-400" />
          </div>
          <p className="text-base font-bold text-amber-400">
            {securityStatus?.total_audit_events ?? 0} Events
          </p>
          <p className="text-[11px] text-slate-500">Immutable trail, credentials sanitized</p>
        </div>
      </div>

      {/* Identity & Role Management Table */}
      <div className="p-5 rounded-2xl bg-slate-900/40 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Users className="w-4 h-4 text-purple-400" />
            <h3 className="text-sm font-semibold text-white tracking-wide">Identity & RBAC Role Assignment</h3>
          </div>
          <span className="text-xs text-slate-500">{totalUsers} System Accounts</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800 uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-2.5 px-3">User ID</th>
                <th className="py-2.5 px-3">Username</th>
                <th className="py-2.5 px-3">Email</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Current Role</th>
                <th className="py-2.5 px-3">Assign New Role</th>
                <th className="py-2.5 px-3 text-right">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-slate-800/40">
                  <td className="py-2.5 px-3 font-mono text-[11px] text-slate-500">#{u.id}</td>
                  <td className="py-2.5 px-3 font-medium text-white">{u.username}</td>
                  <td className="py-2.5 px-3 text-slate-400">{u.email}</td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium border ${
                        u.is_active
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                          : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                      }`}
                    >
                      {u.is_active ? 'Active' : 'Disabled'}
                    </span>
                  </td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono border ${
                        u.role === 'ADMINISTRATOR'
                          ? 'bg-purple-500/20 text-purple-300 border-purple-500/40'
                          : u.role === 'SUPERVISOR'
                          ? 'bg-blue-500/20 text-blue-300 border-blue-500/40'
                          : u.role === 'BANK_EMPLOYEE'
                          ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                          : 'bg-slate-500/20 text-slate-300 border-slate-500/40'
                      }`}
                    >
                      {u.role}
                    </span>
                  </td>
                  <td className="py-2.5 px-3">
                    <select
                      value={u.role}
                      disabled={updatingId === u.id}
                      onChange={(e) => handleRoleChange(u.id, e.target.value)}
                      className="px-2 py-1 text-xs bg-slate-900 border border-slate-700 rounded text-slate-200 focus:outline-none focus:border-purple-500 disabled:opacity-50"
                    >
                      <option value="CUSTOMER">CUSTOMER</option>
                      <option value="BANK_EMPLOYEE">BANK_EMPLOYEE</option>
                      <option value="SUPERVISOR">SUPERVISOR</option>
                      <option value="ADMINISTRATOR">ADMINISTRATOR</option>
                    </select>
                  </td>
                  <td className="py-2.5 px-3 text-right text-slate-500 text-[11px]">
                    {u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
