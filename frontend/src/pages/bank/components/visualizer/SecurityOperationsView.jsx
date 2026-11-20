import React, { useState, useEffect, useCallback } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  Lock,
  Key,
  KeyRound,
  FileText,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Play,
  RotateCw,
  Terminal,
  Layers,
  ArrowRight,
  Eye,
  Radio,
  Server,
  Zap,
} from 'lucide-react';

import {
  fetchVisualizerSecurityOverview,
  executeVisualizerSecurityScenario,
} from '../../../../api/auth';

export const SecurityOperationsView = () => {
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);
  const [activeScenario, setActiveScenario] = useState(null);
  const [selectedAudit, setSelectedAudit] = useState(null);

  const loadSecurityOverview = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchVisualizerSecurityOverview();
      setOverview(data);
    } catch (err) {
      console.error('Failed to load security overview:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSecurityOverview();
  }, [loadSecurityOverview]);

  const handleRunScenario = async (scenarioId) => {
    try {
      setExecuting(true);
      const result = await executeVisualizerSecurityScenario(scenarioId);
      setActiveScenario(result);
      loadSecurityOverview();
    } catch (err) {
      console.error('Scenario execution error:', err);
    } finally {
      setExecuting(false);
    }
  };

  const scenariosList = [
    {
      id: 'SCENARIO_1_VALID_LOGIN',
      title: 'Scenario 1: Valid Employee Login',
      threat: 'None (Legitimate Request)',
      description: 'Verifies correct password against Argon2id memory-hard hash and issues signed JWT bearer token.',
      type: 'NORMAL',
    },
    {
      id: 'SCENARIO_2_INVALID_LOGIN',
      title: 'Scenario 2: Invalid Login Attempt',
      threat: 'Credential Stuffing / Brute Force',
      description: 'Tests incorrect password against Argon2id hash. Safely rejects in constant time with 401.',
      type: 'ATTACK',
    },
    {
      id: 'SCENARIO_3_CUSTOMER_ACCESS_EMPLOYEE',
      title: 'Scenario 3: Customer Role Attempting Employee API',
      threat: 'Privilege Escalation',
      description: 'A valid retail customer token attempts to invoke protected bank employee monitoring routes.',
      type: 'ATTACK',
    },
    {
      id: 'SCENARIO_4_UNAUTHORIZED_BRANCH',
      title: 'Scenario 4: Unauthorized Branch Information Request',
      threat: 'Inter-Branch Impersonation',
      description: 'A forged or unregistered branch secret attempts to query customer records through the Gateway.',
      type: 'ATTACK',
    },
    {
      id: 'SCENARIO_5_EXPIRED_JWT',
      title: 'Scenario 5: Expired JWT Presentation',
      threat: 'Token Replay / Stale Session',
      description: 'Presents a mathematically valid JWT token whose expiration timestamp is in the past.',
      type: 'ATTACK',
    },
    {
      id: 'SCENARIO_6_DUPLICATE_FEDERATION',
      title: 'Scenario 6: Duplicate Federation Request',
      threat: 'Replay Injection',
      description: 'Submits an identical cross-branch request with an already-processed correlation ID.',
      type: 'ATTACK',
    },
    {
      id: 'SCENARIO_7_OUTSIDE_SCOPE',
      title: 'Scenario 7: Request for Information Outside Permitted Scope',
      threat: 'Mass Data Harvesting',
      description: 'Requests unrestricted raw SQL database access outside the whitelisted minimal confirmations.',
      type: 'ATTACK',
    },
  ];

  return (
    <div className="space-y-6">
      {/* View Header */}
      <div className="bg-[#0b152e] border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-emerald-400 text-xs font-bold uppercase tracking-wider mb-1">
              <ShieldCheck className="w-4 h-4" />
              <span>Multi-Layer Security Operations & Threat Defense</span>
            </div>
            <h2 className="text-xl font-extrabold text-white tracking-tight">
              Cryptographic Architecture & Attack Simulation Engine
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Verified backend defense mechanisms: Argon2id password hashing, AES-256-GCM data encryption, JWT RBAC, and TLS transit security.
            </p>
          </div>
        </div>
      </div>

      {/* Security Architecture Component Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Argon2id Password Hashing */}
        <div className="bg-[#0b152e] rounded-2xl border border-slate-800 p-4 shadow-xl space-y-3">
          <div className="flex items-center justify-between">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <KeyRound className="w-5 h-5" />
            </div>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              ONE-WAY HASH
            </span>
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Argon2id Hash Engine</h3>
            <span className="text-[10px] text-slate-400 block font-mono">NON-REVERSIBLE BY DESIGN</span>
          </div>
          <div className="space-y-1 text-[11px] text-slate-300 pt-2 border-t border-slate-800">
            <div className="flex justify-between">
              <span className="text-slate-500">Memory Hardness:</span>
              <span className="font-mono text-emerald-400 font-bold">64 MiB</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Iterations / Cost:</span>
              <span className="font-mono text-white">3 Passes</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Parallelism:</span>
              <span className="font-mono text-white">4 Lanes</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Cryptographic Salt:</span>
              <span className="font-mono text-cyan-400">Unique 16-byte</span>
            </div>
          </div>
          <div className="p-2 rounded-lg bg-emerald-950/20 border border-emerald-800/30 text-[10px] text-emerald-300">
            Passwords are hashed irreversibly to eliminate rainbow table and ASIC cracking.
          </div>
        </div>

        {/* Card 2: AES-256-GCM Data Encryption */}
        <div className="bg-[#0b152e] rounded-2xl border border-slate-800 p-4 shadow-xl space-y-3">
          <div className="flex items-center justify-between">
            <div className="w-9 h-9 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <Lock className="w-5 h-5" />
            </div>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              TWO-WAY ENCRYPT
            </span>
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">AES-256-GCM Cipher</h3>
            <span className="text-[10px] text-slate-400 block font-mono">AUTHENTICATED ENCRYPTION</span>
          </div>
          <div className="space-y-1 text-[11px] text-slate-300 pt-2 border-t border-slate-800">
            <div className="flex justify-between">
              <span className="text-slate-500">Key Length:</span>
              <span className="font-mono text-cyan-400 font-bold">256-bit</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Standard Nonce:</span>
              <span className="font-mono text-white">96-bit Unique</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Auth Tag:</span>
              <span className="font-mono text-emerald-400">128-bit Tamper Tag</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Encrypted Fields:</span>
              <span className="font-mono text-purple-300">7 PII Attributes</span>
            </div>
          </div>
          <div className="p-2 rounded-lg bg-cyan-950/20 border border-cyan-800/30 text-[10px] text-cyan-300">
            Protects sensitive customer delivery addresses, tax IDs, and balances at rest.
          </div>
        </div>

        {/* Card 3: JWT Role-Based Access Control */}
        <div className="bg-[#0b152e] rounded-2xl border border-slate-800 p-4 shadow-xl space-y-3">
          <div className="flex items-center justify-between">
            <div className="w-9 h-9 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
              <Key className="w-5 h-5" />
            </div>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-500/10 text-purple-400 border border-purple-500/30">
              STRICT RBAC
            </span>
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">JWT Bearer & RBAC</h3>
            <span className="text-[10px] text-slate-400 block font-mono">HMAC-SHA256 SIGNED</span>
          </div>
          <div className="space-y-1 text-[11px] text-slate-300 pt-2 border-t border-slate-800">
            <div className="flex justify-between">
              <span className="text-slate-500">Signature Alg:</span>
              <span className="font-mono text-purple-400 font-bold">HS256</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Token Lifetime:</span>
              <span className="font-mono text-white">60 Minutes</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Roles Enforced:</span>
              <span className="font-mono text-white">4 Tier Hierarchy</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Claims Enforced:</span>
              <span className="font-mono text-emerald-400">sub, role, exp</span>
            </div>
          </div>
          <div className="p-2 rounded-lg bg-purple-950/20 border border-purple-800/30 text-[10px] text-purple-300">
            Route-level guards block horizontal and vertical privilege escalation.
          </div>
        </div>

        {/* Card 4: TLS Transport & Audit System */}
        <div className="bg-[#0b152e] rounded-2xl border border-slate-800 p-4 shadow-xl space-y-3">
          <div className="flex items-center justify-between">
            <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <FileText className="w-5 h-5" />
            </div>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
              TAMPER PROOF
            </span>
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">TLS & Audit Engine</h3>
            <span className="text-[10px] text-slate-400 block font-mono">POSTGRESQL PERSISTENCE</span>
          </div>
          <div className="space-y-1 text-[11px] text-slate-300 pt-2 border-t border-slate-800">
            <div className="flex justify-between">
              <span className="text-slate-500">Transit Protection:</span>
              <span className="font-mono text-emerald-400 font-bold">TLS 1.3 / HTTPS</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Sanitization:</span>
              <span className="font-mono text-white">Passwords/Keys Stripped</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Storage Backend:</span>
              <span className="font-mono text-white">PostgreSQL DB</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Replay Protection:</span>
              <span className="font-mono text-cyan-400">Correlation ID</span>
            </div>
          </div>
          <div className="p-2 rounded-lg bg-amber-950/20 border border-amber-800/30 text-[10px] text-amber-300">
            Every authentication, role change, and cross-branch exchange is immutably logged.
          </div>
        </div>
      </div>

      {/* Attack and Defense Demonstration Console */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Scenarios Trigger List */}
        <div className="lg:col-span-1 bg-[#0b152e] rounded-2xl border border-slate-800 p-5 shadow-xl space-y-3">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4 text-red-400" />
              <span>Controlled Attack Scenarios</span>
            </h3>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
              7 Live Tests
            </span>
          </div>

          <div className="space-y-2">
            {scenariosList.map((sc) => {
              const isSelected = activeScenario?.scenario_id === sc.id;
              return (
                <button
                  key={sc.id}
                  disabled={executing}
                  onClick={() => handleRunScenario(sc.id)}
                  className={`w-full text-left p-3 rounded-xl border transition-all duration-200 ${
                    isSelected
                      ? 'bg-slate-900 border-cyan-400 ring-2 ring-cyan-500/20 shadow-md'
                      : 'bg-slate-950/40 border-slate-800 hover:border-slate-700 hover:bg-slate-900/60'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span
                      className={`text-[10px] font-bold font-mono px-1.5 py-0.5 rounded ${
                        sc.type === 'NORMAL'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                          : 'bg-red-500/10 text-red-400 border border-red-500/30'
                      }`}
                    >
                      {sc.threat}
                    </span>
                    <Play className="w-3 h-3 text-cyan-400" />
                  </div>
                  <h4 className="text-xs font-bold text-white tracking-tight">{sc.title}</h4>
                  <p className="text-[10px] text-slate-400 mt-1 line-clamp-2">{sc.description}</p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Live Scenario Inspection Canvas & Defense Flow */}
        <div className="lg:col-span-2 bg-[#0b152e] rounded-2xl border border-slate-800 p-5 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                <Terminal className="w-4 h-4 text-cyan-400" />
                <span>Defense Inspector & Cryptographic Verification</span>
              </h3>
              {activeScenario && (
                <span
                  className={`px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
                    activeScenario.defense_status === 'ACCEPTED'
                      ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/40'
                      : 'bg-red-500/15 text-red-300 border border-red-500/40'
                  }`}
                >
                  {activeScenario.defense_status === 'ACCEPTED' ? '✓ Accepted (Authorized)' : '🛡️ Defended (Attack Blocked)'}
                </span>
              )}
            </div>

            {activeScenario ? (
              <div className="space-y-4">
                {/* Header overview banner */}
                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <h4 className="text-base font-extrabold text-white tracking-tight">{activeScenario.title}</h4>
                    <span className="text-xs font-mono font-bold text-cyan-400 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800/40">
                      Reason: {activeScenario.reason_code}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300">{activeScenario.outcome_summary}</p>
                </div>

                {/* Defense Verification Flow Steps */}
                <div>
                  <h5 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">
                    Sequential Security Checks:
                  </h5>
                  <div className="space-y-2">
                    {activeScenario.checks.map((ck, i) => (
                      <div
                        key={i}
                        className="flex items-start space-x-3 p-3 rounded-xl bg-slate-900/50 border border-slate-800"
                      >
                        <div className="mt-0.5">
                          {ck.status === 'PASS' ? (
                            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                          ) : ck.status === 'BLOCKED' ? (
                            <ShieldAlert className="w-4 h-4 text-red-400" />
                          ) : ck.status === 'HALTED' ? (
                            <XCircle className="w-4 h-4 text-orange-400" />
                          ) : (
                            <FileText className="w-4 h-4 text-cyan-400" />
                          )}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-white">{ck.component}</span>
                            <span
                              className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded ${
                                ck.status === 'PASS'
                                  ? 'bg-emerald-500/10 text-emerald-400'
                                  : ck.status === 'BLOCKED'
                                  ? 'bg-red-500/10 text-red-400'
                                  : 'bg-cyan-500/10 text-cyan-400'
                              }`}
                            >
                              {ck.status}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-400 mt-0.5">{ck.detail}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Sanitized Payload & Audit Log Info */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                    <span className="text-[10px] font-bold uppercase text-slate-400 block mb-1">
                      Sanitized Inspection Envelope:
                    </span>
                    <pre className="text-[10px] font-mono text-cyan-300 overflow-x-auto">
                      {JSON.stringify(activeScenario.sanitized_input, null, 2)}
                    </pre>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                    <span className="text-[10px] font-bold uppercase text-slate-400 block mb-1">
                      Authoritative PostgreSQL Audit:
                    </span>
                    <div className="space-y-1">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Audit ID:</span>
                        <span className="font-mono text-emerald-400 font-bold">{activeScenario.audit_id}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Storage:</span>
                        <span className="font-mono text-white">audit_logs table</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">PII Leaks:</span>
                        <span className="font-bold text-emerald-400">ZERO (Strictly Redacted)</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-16 text-slate-500 space-y-2">
                <ShieldCheck className="w-12 h-12 mx-auto text-slate-600" />
                <h4 className="text-sm font-bold text-slate-400">Select a Security Scenario to Execute</h4>
                <p className="text-xs max-w-md mx-auto">
                  Click any of the 7 controlled attack/defense scenarios on the left to observe how the real backend engines defend each threat vector.
                </p>
              </div>
            )}
          </div>

          <div className="pt-4 border-t border-slate-800 flex items-center justify-between text-[10px] text-slate-500 font-mono">
            <span>Argon2id (Hash) ≠ AES-256-GCM (Encryption)</span>
            <span>Zero Real PII or Keys Exposed</span>
          </div>
        </div>
      </div>

      {/* Recent Security Audit Logs Table */}
      <div className="bg-[#0b152e] rounded-2xl border border-slate-800 p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
              <FileText className="w-4 h-4 text-emerald-400" />
              <span>Recent Security & Authentication Audit Logs</span>
            </h3>
            <span className="text-xs text-slate-400">Immutable trail persisted to PostgreSQL</span>
          </div>
          <button
            onClick={loadSecurityOverview}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-900 border border-slate-700 text-slate-300 hover:text-white hover:bg-slate-800 transition"
          >
            <RotateCw className="w-3.5 h-3.5" />
            <span>Refresh Logs</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider">
                <th className="py-2.5 px-3">Audit Event ID</th>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Action</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Sanitized Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
              {!overview?.recent_audit_logs || overview.recent_audit_logs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-slate-500 font-sans">
                    No recent audit logs available. Execute a scenario above to generate an audit event.
                  </td>
                </tr>
              ) : (
                overview.recent_audit_logs.slice(0, 8).map((a) => (
                  <tr key={a.audit_id} className="hover:bg-slate-900/50 transition">
                    <td className="py-2.5 px-3 text-emerald-400 font-bold">{a.audit_id}</td>
                    <td className="py-2.5 px-3 text-slate-400 font-sans text-xs">
                      {a.timestamp ? new Date(a.timestamp).toLocaleTimeString() : 'Recent'}
                    </td>
                    <td className="py-2.5 px-3 text-white font-bold">{a.action}</td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          a.status === 'SUCCESS' || a.status === 'IDEMPOTENT_CACHED'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                            : 'bg-red-500/10 text-red-400 border border-red-500/30'
                        }`}
                      >
                        {a.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-300 font-sans text-xs truncate max-w-[260px]">
                      {a.details}
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
