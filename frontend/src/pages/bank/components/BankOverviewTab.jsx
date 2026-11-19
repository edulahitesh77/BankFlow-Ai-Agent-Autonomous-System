import React from 'react';
import {
  FileText,
  Clock,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Users,
  CreditCard,
  TrendingUp,
  Activity,
  ArrowRight,
  ShieldCheck,
  Building2,
} from 'lucide-react';

export const BankOverviewTab = ({ data, onSelectTab, onSelectRequest }) => {
  if (!data) return null;

  const { summary, request_distribution, status_distribution, service_demand, recent_activity } = data;

  const summaryCards = [
    {
      title: 'Total Requests',
      value: summary.total_requests,
      icon: FileText,
      color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
      actionTab: 'requests',
    },
    {
      title: 'New Submissions',
      value: summary.new_requests,
      icon: Clock,
      color: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30',
      actionTab: 'pending',
    },
    {
      title: 'Pending Processing',
      value: summary.pending_requests,
      icon: Activity,
      color: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
      actionTab: 'pending',
    },
    {
      title: 'Human Review Required',
      value: summary.human_review_requests,
      icon: ShieldAlert,
      color: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
      actionTab: 'review',
    },
    {
      title: 'Needs Correction',
      value: summary.needs_correction_requests,
      icon: AlertTriangle,
      color: 'text-orange-400 bg-orange-500/10 border-orange-500/30',
      actionTab: 'correction',
    },
    {
      title: 'Completed Requests',
      value: summary.completed_requests,
      icon: CheckCircle2,
      color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
      actionTab: 'requests',
    },
    {
      title: 'Rejected Requests',
      value: summary.rejected_requests,
      icon: XCircle,
      color: 'text-rose-400 bg-rose-500/10 border-rose-500/30',
      actionTab: 'rejected',
    },
    {
      title: 'Total Customers',
      value: summary.total_customers,
      icon: Users,
      color: 'text-purple-400 bg-purple-500/10 border-purple-500/30',
      actionTab: 'customers',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Top Welcome Banner */}
      <div className="bg-gradient-to-r from-[#0d1733] via-[#0f1f45] to-[#0a382e] border border-slate-800 rounded-2xl p-6 sm:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-xl relative overflow-hidden">
        <div className="relative z-10 space-y-2">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
            <span>BankFlow AI Multi-Agent Core • Supervision Active</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Bank Operations & Oversight Console
          </h1>
          <p className="text-sm text-slate-300 max-w-2xl leading-relaxed">
            Real-time management for synthetic customer service workflows, human supervisory exception gates,
            correction routing, and regulatory audit compliance.
          </p>
        </div>

        <div className="relative z-10 flex flex-wrap items-center gap-3">
          <button
            onClick={() => onSelectTab('review')}
            className="px-4 py-2.5 rounded-xl font-semibold text-xs text-slate-950 bg-emerald-400 hover:bg-emerald-300 transition flex items-center space-x-2 shadow-lg shadow-emerald-500/20"
          >
            <ShieldAlert className="w-4 h-4" />
            <span>Review Queue ({summary.human_review_requests})</span>
          </button>
          <button
            onClick={() => onSelectTab('requests')}
            className="px-4 py-2.5 rounded-xl font-semibold text-xs text-slate-200 bg-slate-900/80 hover:bg-slate-800 border border-slate-700 transition flex items-center space-x-2"
          >
            <span>All Requests</span>
            <ArrowRight className="w-3.5 h-3.5 text-emerald-400" />
          </button>
        </div>
      </div>

      {/* Summary Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {summaryCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              onClick={() => onSelectTab(card.actionTab)}
              className="bg-[#0b132b] hover:bg-[#0e1a38] border border-slate-800 hover:border-slate-700 rounded-xl p-4 sm:p-5 transition cursor-pointer group shadow-lg flex flex-col justify-between"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">{card.title}</span>
                <div className={`p-2 rounded-lg border ${card.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-4 flex items-baseline justify-between">
                <span className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                  {card.value}
                </span>
                <span className="text-[11px] font-semibold text-emerald-400 opacity-0 group-hover:opacity-100 transition flex items-center space-x-0.5">
                  <span>View</span>
                  <ArrowRight className="w-3 h-3" />
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Middle Analytics Section: Service Breakdown & Demand */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Service Type Distribution */}
        <div className="bg-[#0b132b] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4 lg:col-span-1">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span>Service Type Breakdown</span>
            </h3>
            <span className="text-xs text-slate-400 font-mono">{summary.total_requests} Total</span>
          </div>

          <div className="space-y-4 text-xs pt-1">
            {Object.entries(request_distribution).map(([service, count]) => {
              const pct = summary.total_requests > 0 ? Math.round((count / summary.total_requests) * 100) : 0;
              return (
                <div key={service} className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-slate-300">{service.replace(/_/g, ' ')}</span>
                    <span className="text-slate-400 font-mono">
                      {count} <span className="text-emerald-400">({pct}%)</span>
                    </span>
                  </div>
                  <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
                    <div
                      className="h-full bg-gradient-to-r from-emerald-500 to-cyan-400 rounded-full transition-all duration-500"
                      style={{ width: `${pct}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Status Distribution */}
        <div className="bg-[#0b132b] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4 lg:col-span-1">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              <span>Request Status Distribution</span>
            </h3>
            <span className="text-xs text-slate-400">All Workflow States</span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs pt-1">
            {Object.entries(status_distribution).map(([status, count]) => (
              <div
                key={status}
                className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 flex items-center justify-between"
              >
                <span className="text-[11px] text-slate-400 font-medium truncate mr-1">
                  {status.replace(/_/g, ' ')}
                </span>
                <span
                  className={`text-xs font-bold font-mono px-1.5 py-0.5 rounded ${
                    count > 0 ? 'bg-emerald-500/10 text-emerald-400' : 'text-slate-500'
                  }`}
                >
                  {count}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Service Demand Ranking */}
        <div className="bg-[#0b132b] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4 lg:col-span-1">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <CreditCard className="w-4 h-4 text-purple-400" />
              <span>Service Demand Ranking</span>
            </h3>
            <span className="text-xs text-emerald-400 font-semibold">Live Traffic</span>
          </div>

          <div className="space-y-3 text-xs pt-1">
            {service_demand.map((item, idx) => (
              <div
                key={item.service_type}
                className="p-3 bg-slate-900/60 rounded-xl border border-slate-800 flex items-center justify-between"
              >
                <div className="flex items-center space-x-3">
                  <span className="w-6 h-6 rounded-full bg-slate-800 text-slate-300 flex items-center justify-center font-bold text-[11px]">
                    #{idx + 1}
                  </span>
                  <div>
                    <span className="font-semibold text-white block">
                      {item.service_type.replace(/_/g, ' ')}
                    </span>
                    <span className="text-[10px] text-slate-400">Demand Share: {item.percentage}%</span>
                  </div>
                </div>
                <div className="text-right font-mono font-bold text-emerald-400 text-sm">
                  {item.count}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Section: Recent Compliance Audit Activity */}
      <div className="bg-[#0b132b] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <h3 className="text-base font-bold text-white flex items-center space-x-2">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              <span>Recent Operational Audit Stream</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Immutable ledger of customer requests, employee decisions, and state transitions.
            </p>
          </div>
          <button
            onClick={() => onSelectTab('audit')}
            className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 underline"
          >
            View Full Audit Logs →
          </button>
        </div>

        {recent_activity && recent_activity.length > 0 ? (
          <div className="divide-y divide-slate-800 text-xs">
            {recent_activity.map((act) => (
              <div key={act.id} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-start space-x-3">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold mt-0.5 border ${
                      act.action.includes('REJECT')
                        ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                        : act.action.includes('CORRECTION')
                        ? 'bg-orange-500/10 text-orange-400 border-orange-500/30'
                        : act.action.includes('REVIEW')
                        ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                        : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                    }`}
                  >
                    {act.action}
                  </span>
                  <div>
                    <span className="font-semibold text-white">{act.actor}</span>
                    <span className="text-slate-400 ml-1.5">({act.role})</span>
                    <p className="text-slate-300 text-xs mt-0.5">{act.description}</p>
                  </div>
                </div>

                <div className="text-slate-500 text-[11px] sm:text-right whitespace-nowrap font-mono">
                  {new Date(act.timestamp).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center text-slate-500 text-xs">
            No audit activities recorded yet.
          </div>
        )}
      </div>
    </div>
  );
};
