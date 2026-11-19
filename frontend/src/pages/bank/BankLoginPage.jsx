import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { loginBank } from '../../api/auth';
import {
  ShieldAlert,
  ShieldCheck,
  Building2,
  Lock,
  ArrowRight,
  AlertCircle,
  CheckCircle,
  FileText,
  KeyRound,
  Activity,
} from 'lucide-react';

export const BankLoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [formData, setFormData] = useState({
    employee_id_or_username: '',
    password: '',
  });

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    if (errorMessage) setErrorMessage('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setSuccessMessage('');

    if (!formData.employee_id_or_username.trim() || !formData.password) {
      setErrorMessage('Please enter your Employee ID / Username and Password.');
      return;
    }

    setLoading(true);
    try {
      const data = await loginBank({
        employee_id_or_username: formData.employee_id_or_username.trim(),
        password: formData.password,
      });

      setSuccessMessage('Staff authorization verified. Opening Bank Dashboard...');
      login(data.access_token, {
        id: data.user_id,
        username: data.username,
        role: data.role,
      });

      setTimeout(() => {
        navigate('/bank/dashboard');
      }, 700);
    } catch (err) {
      setErrorMessage(err.message || 'Invalid employee credentials. Access denied.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#070d1e] text-slate-100 flex flex-col justify-between relative overflow-hidden">
      {/* Background radial glow */}
      <div className="absolute top-0 right-1/4 w-[600px] h-[600px] bg-emerald-500/5 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-0 left-10 w-[500px] h-[500px] bg-blue-600/5 rounded-full blur-3xl pointer-events-none"></div>

      {/* Top Bar */}
      <header className="border-b border-slate-800/80 bg-[#070d1e]/80 backdrop-blur-md relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="w-10 h-10 bg-emerald-500/10 border border-emerald-500/30 rounded-xl flex items-center justify-center text-emerald-400 group-hover:border-emerald-400 transition">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <span className="text-lg font-bold text-white tracking-tight">BankFlow</span>
              <span className="text-lg font-light text-emerald-400 ml-1">Staff Portal</span>
            </div>
          </Link>

          <Link
            to="/customer/login"
            className="text-xs font-semibold text-slate-400 hover:text-white px-3 py-1.5 rounded-lg border border-slate-800 hover:border-slate-700 transition"
          >
            ← Switch to Retail Customer Login
          </Link>
        </div>
      </header>

      {/* Main Dual-Column Content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12 flex-1 flex items-center justify-center relative z-10 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center w-full">
          {/* Left Column: Branding and Features */}
          <div className="lg:col-span-6 space-y-6">
            <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold">
              <ShieldCheck className="w-4 h-4" />
              <span>Internal Bank Operations Management</span>
            </div>

            <h1 className="text-4xl sm:text-5xl font-black text-white tracking-tight leading-tight">
              Seamless <span className="text-emerald-400">Employee Management</span> Solution
            </h1>

            <p className="text-slate-400 text-base leading-relaxed">
              Streamline your workforce operations and banking workflow automation with our high-fidelity dashboard.
              Manage request queues, customer verification, and multi-agent service routing in one secure place.
            </p>

            {/* Feature Pills */}
            <div className="space-y-3.5 pt-2">
              <div className="flex items-center space-x-3 text-sm text-slate-300">
                <div className="w-8 h-8 rounded-lg bg-slate-800/80 border border-slate-700 flex items-center justify-center text-emerald-400">
                  <FileText className="w-4 h-4" />
                </div>
                <span>Employee Records & Staff Directory</span>
              </div>
              <div className="flex items-center space-x-3 text-sm text-slate-300">
                <div className="w-8 h-8 rounded-lg bg-slate-800/80 border border-slate-700 flex items-center justify-center text-emerald-400">
                  <KeyRound className="w-4 h-4" />
                </div>
                <span>Role-Based Access Control (RBAC) & Argon2id Security</span>
              </div>
              <div className="flex items-center space-x-3 text-sm text-slate-300">
                <div className="w-8 h-8 rounded-lg bg-slate-800/80 border border-slate-700 flex items-center justify-center text-emerald-400">
                  <Activity className="w-4 h-4" />
                </div>
                <span>Real-Time Audit Trail & Multi-Agent Oversight</span>
              </div>
            </div>

            {/* Default Dev Account Hint */}
            <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400 space-y-1">
              <div className="font-semibold text-slate-300">Development Seed Account:</div>
              <div>Username: <code className="text-emerald-400">bank_admin</code> or Employee ID: <code className="text-emerald-400">EMP-SYN-0001</code></div>
              <div>Password: <code className="text-emerald-400">Employee@2026!</code> (Configurable in .env)</div>
            </div>
          </div>

          {/* Right Column: High-Fidelity Login Card */}
          <div className="lg:col-span-6 w-full max-w-md mx-auto">
            <div className="bg-[#0f172a]/90 backdrop-blur-xl p-8 rounded-3xl border border-slate-800 shadow-2xl shadow-black/60 relative">
              <div className="text-center mb-6">
                <h2 className="text-2xl font-extrabold text-white">Welcome Back</h2>
                <p className="text-xs text-slate-400 mt-1">
                  Enter your credentials to access the internal banking system
                </p>
              </div>

              {/* Error Banner */}
              {errorMessage && (
                <div className="mb-5 p-3.5 rounded-xl bg-red-950/50 border border-red-800/80 flex items-start space-x-3 text-red-200 text-xs animate-fade-in">
                  <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-red-400" />
                  <div className="flex-1 font-medium">{errorMessage}</div>
                </div>
              )}

              {/* Success Banner */}
              {successMessage && (
                <div className="mb-5 p-3.5 rounded-xl bg-emerald-950/50 border border-emerald-800/80 flex items-start space-x-3 text-emerald-200 text-xs animate-fade-in">
                  <CheckCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-emerald-400" />
                  <div className="flex-1 font-medium">{successMessage}</div>
                </div>
              )}

              <form className="space-y-5" onSubmit={handleSubmit}>
                {/* Employee ID or Username */}
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
                    Employee ID or Username
                  </label>
                  <div className="relative rounded-xl shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                      <Building2 className="w-4 h-4" />
                    </div>
                    <input
                      name="employee_id_or_username"
                      type="text"
                      required
                      placeholder="e.g. EMP-SYN-0001 or bank_admin"
                      value={formData.employee_id_or_username}
                      onChange={handleChange}
                      className="block w-full pl-10 pr-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-white text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition"
                    />
                  </div>
                </div>

                {/* Password */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                      Password
                    </label>
                    <span className="text-xs text-slate-500">Forgot Password? Contact Admin</span>
                  </div>
                  <div className="relative rounded-xl shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                      <Lock className="w-4 h-4" />
                    </div>
                    <input
                      name="password"
                      type="password"
                      required
                      placeholder="••••••••••••"
                      value={formData.password}
                      onChange={handleChange}
                      className="block w-full pl-10 pr-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-white text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition"
                    />
                  </div>
                </div>

                {/* Notice: No public registration */}
                <div className="flex items-center space-x-2 text-xs text-slate-400 pt-1">
                  <ShieldAlert className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  <span>Public registration disabled. Accounts provisioned by administrator.</span>
                </div>

                {/* Submit Button */}
                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full flex items-center justify-center space-x-2 py-3.5 px-4 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-xl text-sm transition shadow-lg shadow-emerald-500/25 disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    {loading ? (
                      <>
                        <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin"></div>
                        <span>Authenticating staff credentials...</span>
                      </>
                    ) : (
                      <>
                        <span>Login to Dashboard</span>
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </div>
              </form>

              {/* Bottom Support & Security Meta */}
              <div className="mt-6 pt-5 border-t border-slate-800 text-center space-y-1 text-xs text-slate-500">
                <div>Employee Support: <span className="text-slate-400">operations@bankflow.synthetic</span></div>
                <div className="text-[11px] text-slate-600">v1.0.0 • 256-BIT ARGON2ID • SECURE TLS</div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 py-4 text-center text-xs text-slate-600">
        BankFlow AI – Internal Bank Staff & Operations System. Unauthorized access is monitored and logged.
      </footer>
    </div>
  );
};
