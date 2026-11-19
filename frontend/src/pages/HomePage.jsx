import React from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  Building2,
  Users,
  Lock,
  ArrowRight,
  Cpu,
  CheckCircle2,
} from 'lucide-react';

export const HomePage = () => {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-between">
      {/* Top Navigation */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center text-white shadow-md shadow-blue-500/20">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xl font-bold text-slate-900 tracking-tight">BankFlow</span>
              <span className="text-xl font-light text-blue-600 ml-1">AI</span>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <Link
              to="/customer/login"
              className="text-sm font-semibold text-slate-600 hover:text-blue-600 px-3 py-1.5 transition"
            >
              Customer Portal
            </Link>
            <Link
              to="/bank/login"
              className="text-sm font-semibold text-white bg-slate-900 hover:bg-slate-800 px-4 py-2 rounded-xl transition shadow-sm"
            >
              Staff Portal
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 flex-1 flex flex-col justify-center">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <div className="inline-flex items-center space-x-2 px-3 py-1 bg-blue-50 border border-blue-200 rounded-full text-xs font-semibold text-blue-700 mb-4">
            <Cpu className="w-3.5 h-3.5" />
            <span>Intelligent Multi-Agent Banking Service Automation</span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight leading-tight">
            Dual Authentication & Multi-Agent Architecture
          </h1>
          <p className="mt-4 text-base sm:text-lg text-slate-600 leading-relaxed">
            Choose your access portal below. BankFlow AI enforces strict role separation between retail banking customers and internal bank personnel.
          </p>
        </div>

        {/* Dual Portals Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto w-full">
          {/* Customer Portal Card */}
          <div className="bg-white rounded-3xl p-8 border border-slate-200/80 shadow-xl shadow-slate-200/50 flex flex-col justify-between hover:border-blue-300 transition duration-300 relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-40 h-40 bg-blue-100/40 rounded-full -mr-16 -mt-16 pointer-events-none group-hover:scale-110 transition duration-500"></div>

            <div>
              <div className="w-14 h-14 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mb-6 border border-blue-100">
                <Users className="w-7 h-7" />
              </div>
              <div className="inline-block text-xs font-bold uppercase tracking-wider text-blue-600 bg-blue-50 px-2.5 py-1 rounded-md mb-2">
                Retail Banking
              </div>
              <h2 className="text-2xl font-bold text-slate-900">Customer Portal</h2>
              <p className="text-sm text-slate-600 mt-2 leading-relaxed">
                Self-service banking for account holders. Register, view synthetic accounts, and submit automated service requests.
              </p>

              <div className="mt-6 space-y-2.5 text-xs text-slate-600">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-blue-600 flex-shrink-0" />
                  <span>Self-service customer registration with Argon2id encryption</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-blue-600 flex-shrink-0" />
                  <span>Synthetic accounts & personal profile isolation</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-blue-600 flex-shrink-0" />
                  <span>Cheque book, debit card, and address service requests</span>
                </div>
              </div>
            </div>

            <div className="mt-8 pt-6 border-t border-slate-100 flex flex-col sm:flex-row gap-3">
              <Link
                to="/customer/login"
                className="flex-1 inline-flex items-center justify-center space-x-2 px-5 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-sm transition shadow-md shadow-blue-500/20"
              >
                <span>Customer Sign In</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/customer/register"
                className="inline-flex items-center justify-center px-4 py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-xl text-sm transition"
              >
                <span>Register</span>
              </Link>
            </div>
          </div>

          {/* Bank Employee Portal Card */}
          <div className="bg-slate-900 rounded-3xl p-8 border border-slate-800 shadow-2xl flex flex-col justify-between hover:border-emerald-500/50 transition duration-300 relative overflow-hidden group text-white">
            <div className="absolute top-0 right-0 w-40 h-40 bg-emerald-500/10 rounded-full -mr-16 -mt-16 pointer-events-none group-hover:scale-110 transition duration-500"></div>

            <div>
              <div className="w-14 h-14 bg-slate-800 text-emerald-400 rounded-2xl flex items-center justify-center mb-6 border border-slate-700">
                <Building2 className="w-7 h-7" />
              </div>
              <div className="inline-block text-xs font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-md mb-2 border border-emerald-500/20">
                Authorized Staff Only
              </div>
              <h2 className="text-2xl font-bold text-white">Bank Staff Portal</h2>
              <p className="text-sm text-slate-400 mt-2 leading-relaxed">
                Restricted portal for bank employees, branch supervisors, and operations staff overseeing multi-agent workflows.
              </p>

              <div className="mt-6 space-y-2.5 text-xs text-slate-300">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  <span>Controlled staff provisioning (No public registration)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  <span>Employee ID / username role-based authentication</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  <span>Immutable audit logging & multi-agent routing oversight</span>
                </div>
              </div>
            </div>

            <div className="mt-8 pt-6 border-t border-slate-800 flex flex-col sm:flex-row gap-3">
              <Link
                to="/bank/login"
                className="flex-1 inline-flex items-center justify-center space-x-2 px-5 py-3 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold rounded-xl text-sm transition shadow-lg shadow-emerald-500/20"
              >
                <span>Staff Portal Sign In</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <div className="flex items-center justify-center px-3 py-2 text-xs text-slate-400 bg-slate-800/80 rounded-xl border border-slate-700/50">
                <Lock className="w-3.5 h-3.5 mr-1.5 text-slate-400" />
                <span>Internal Only</span>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        <p>BankFlow AI – Educational Banking Service Automation Simulation.</p>
        <p className="mt-1 text-slate-400">Phase 2: Customer and Bank Employee Authentication System.</p>
      </footer>
    </div>
  );
};
