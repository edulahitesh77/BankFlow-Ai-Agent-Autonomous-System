import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  fetchBankProfile,
  fetchBankDashboard,
  fetchBankRequestDetails,
  submitReviewDecision,
  submitCorrectionRequest,
} from '../../api/auth';
import {
  Building2,
  ShieldCheck,
  User,
  Users,
  Activity,
  LogOut,
  Layers,
  Cpu,
  AlertCircle,
  CheckCircle2,
  FileCheck,
  FileText,
  Clock,
  ShieldAlert,
  AlertTriangle,
  XCircle,
  Menu,
  X,
  Radio,
  Lock,
  Network,
} from 'lucide-react';

import { BankOverviewTab } from './components/BankOverviewTab';
import { AllRequestsTab } from './components/AllRequestsTab';
import { PendingRequestsTab } from './components/PendingRequestsTab';
import { HumanReviewTab } from './components/HumanReviewTab';
import { NeedsCorrectionTab } from './components/NeedsCorrectionTab';
import { RejectedRequestsTab } from './components/RejectedRequestsTab';
import { CustomerRecordsTab } from './components/CustomerRecordsTab';
import { AgentMonitoringTab } from './components/AgentMonitoringTab';
import { AgentCommunicationTab } from './components/AgentCommunicationTab';
import { AgentRecoveryTab } from './components/AgentRecoveryTab';
import { BranchFederationTab } from './components/BranchFederationTab';
import { AdminManagementTab } from './components/AdminManagementTab';
import { AuditLogsTab } from './components/AuditLogsTab';
import { RequestDetailModal } from './components/RequestDetailModal';
import { ReviewActionModal } from './components/ReviewActionModal';
import { CorrectionActionModal } from './components/CorrectionActionModal';

export const BankDashboardPage = () => {
  const { user, role, logout } = useAuth();
  const navigate = useNavigate();

  const [profile, setProfile] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Modals state
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [inspectModalOpen, setInspectModalOpen] = useState(false);
  const [reviewModalRequest, setReviewModalRequest] = useState(null);
  const [correctionModalRequest, setCorrectionModalRequest] = useState(null);

  const effectiveRole = role || user?.role || profile?.role;

  const loadInitialData = async () => {
    try {
      const [profileData, dashData] = await Promise.all([
        fetchBankProfile(),
        fetchBankDashboard(),
      ]);
      setProfile(profileData);
      setDashboardData(dashData);
    } catch (err) {
      setError(err.message || 'Failed to load bank portal.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/bank/login');
  };

  const handleOpenDetailModal = async (requestId) => {
    try {
      const fullDetail = await fetchBankRequestDetails(requestId);
      setSelectedRequest(fullDetail);
      setInspectModalOpen(true);
    } catch (err) {
      console.error('Failed to load request detail:', err);
    }
  };

  const handleOpenReview = (req) => {
    setReviewModalRequest(req);
  };

  const handleOpenCorrection = (req) => {
    setCorrectionModalRequest(req);
  };

  const handleReviewSubmit = async (reviewData) => {
    if (!reviewModalRequest) return;
    await submitReviewDecision(reviewModalRequest.request_id, reviewData);
    // Reload dashboard metrics & update inspect modal if open
    const dashData = await fetchBankDashboard();
    setDashboardData(dashData);
    if (selectedRequest && selectedRequest.request_id === reviewModalRequest.request_id) {
      const updated = await fetchBankRequestDetails(reviewModalRequest.request_id);
      setSelectedRequest(updated);
    }
  };

  const handleCorrectionSubmit = async (correctionData) => {
    if (!correctionModalRequest) return;
    await submitCorrectionRequest(correctionModalRequest.request_id, correctionData);
    // Reload dashboard metrics & update inspect modal if open
    const dashData = await fetchBankDashboard();
    setDashboardData(dashData);
    if (selectedRequest && selectedRequest.request_id === correctionModalRequest.request_id) {
      const updated = await fetchBankRequestDetails(correctionModalRequest.request_id);
      setSelectedRequest(updated);
    }
  };

  const menuItems = [
    { id: 'overview', label: 'Dashboard', icon: Activity },
    { id: 'requests', label: 'All Requests', icon: FileText, badge: dashboardData?.summary?.total_requests },
    { id: 'pending', label: 'Pending Requests', icon: Clock, badge: dashboardData?.summary?.pending_requests },
    {
      id: 'review',
      label: 'Human Review',
      icon: ShieldAlert,
      badge: dashboardData?.summary?.human_review_requests,
      badgeColor: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
    },
    {
      id: 'correction',
      label: 'Needs Correction',
      icon: AlertTriangle,
      badge: dashboardData?.summary?.needs_correction_requests,
      badgeColor: 'bg-orange-500/20 text-orange-300 border-orange-500/40',
    },
    { id: 'rejected', label: 'Rejected Requests', icon: XCircle },
    { id: 'customers', label: 'Customer Records', icon: Users, badge: dashboardData?.summary?.total_customers },
    { id: 'agents', label: 'Agent Monitoring', icon: Cpu },
    { id: 'communication', label: 'Agent Communication', icon: Radio },
    { id: 'recovery', label: 'Recovery & Reliability', icon: ShieldAlert },
    { id: 'federation', label: 'Branch Federation', icon: Network },
    { id: 'audit', label: 'Audit Logs', icon: ShieldCheck },
    ...(effectiveRole === 'ADMINISTRATOR' ? [{ id: 'admin', label: 'Administration', icon: Lock }] : []),
  ];

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#070d1e] text-slate-100">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-10 h-10 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm text-slate-400 font-medium">Initializing Bank Operations Console...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#070d1e] text-slate-100 flex flex-col">
      {/* Top Navigation Bar */}
      <header className="border-b border-slate-800 bg-[#070d1e]/95 backdrop-blur-md sticky top-0 z-30">
        <div className="px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
            >
              <Menu className="w-5 h-5" />
            </button>

            <div className="w-10 h-10 bg-emerald-500/10 border border-emerald-500/30 rounded-xl flex items-center justify-center text-emerald-400">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <span className="text-lg font-bold text-white tracking-tight">BankFlow</span>
              <span className="text-lg font-light text-emerald-400 ml-1">Staff Admin</span>
              <span className="hidden sm:inline-block ml-3 px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                Central Operations Console
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="hidden md:flex flex-col text-right">
              <span className="text-sm font-bold text-white">{profile?.full_name || user?.username}</span>
              <div className="flex items-center justify-end space-x-1.5 text-xs text-slate-400">
                <span className="font-mono text-emerald-400">{profile?.employee_code}</span>
                <span>•</span>
                <span>{profile?.designation || 'Bank Officer'}</span>
              </div>
            </div>

            <button
              onClick={handleLogout}
              className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold text-slate-300 hover:text-white bg-slate-900 hover:bg-slate-800 border border-slate-700 hover:border-slate-600 transition"
            >
              <LogOut className="w-4 h-4 text-emerald-400" />
              <span>Log Out</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Workspace with Sidebar */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar Navigation */}
        <aside
          className={`fixed inset-y-0 left-0 z-40 w-64 bg-[#091126] border-r border-slate-800 flex flex-col justify-between transform transition-transform duration-200 ease-in-out lg:relative lg:translate-x-0 ${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          {/* Mobile close button */}
          <div className="p-4 lg:hidden flex justify-end">
            <button
              onClick={() => setSidebarOpen(false)}
              className="p-1.5 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Links */}
          <div className="p-4 space-y-1.5 flex-1 overflow-y-auto">
            <div className="px-3 py-2 text-[11px] font-bold uppercase tracking-wider text-slate-500">
              Operations Center
            </div>
            {menuItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveTab(item.id);
                    setSidebarOpen(false);
                  }}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition ${
                    isActive
                      ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 shadow-lg shadow-emerald-500/5'
                      : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                  }`}
                >
                  <div className="flex items-center space-x-2.5">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-500'}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge !== undefined && item.badge > 0 && (
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                        item.badgeColor || 'bg-slate-800 border-slate-700 text-slate-300'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Sidebar Employee Badge */}
          <div className="p-4 border-t border-slate-800 bg-[#070d1e]/60">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold text-xs">
                {profile?.full_name?.charAt(0) || 'E'}
              </div>
              <div className="flex-1 min-w-0">
                <span className="text-xs font-bold text-white block truncate">{profile?.full_name}</span>
                <span className="text-[10px] text-slate-500 font-mono block truncate">
                  {profile?.department || 'Operations'} • {profile?.branch_id || 'Digital'}
                </span>
              </div>
            </div>
          </div>
        </aside>

        {/* Backdrop for mobile */}
        {sidebarOpen && (
          <div
            onClick={() => setSidebarOpen(false)}
            className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-30 lg:hidden"
          ></div>
        )}

        {/* Main Content Workspace */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto space-y-6">
            {error && (
              <div className="p-4 rounded-xl bg-red-950/60 border border-red-800 flex items-center space-x-3 text-red-200 text-sm">
                <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-400" />
                <span>{error}</span>
              </div>
            )}

            {/* Tab Rendering */}
            {activeTab === 'overview' && (
              <BankOverviewTab
                data={dashboardData}
                onSelectTab={setActiveTab}
                onSelectRequest={handleOpenDetailModal}
              />
            )}

            {activeTab === 'requests' && (
              <AllRequestsTab
                onSelectRequest={handleOpenDetailModal}
                onOpenReview={handleOpenReview}
                onOpenCorrection={handleOpenCorrection}
                onInspectCustomer={(custId) => {
                  setActiveTab('customers');
                }}
              />
            )}

            {activeTab === 'pending' && (
              <PendingRequestsTab
                onSelectRequest={handleOpenDetailModal}
                onOpenReview={handleOpenReview}
                onOpenCorrection={handleOpenCorrection}
              />
            )}

            {activeTab === 'review' && (
              <HumanReviewTab
                onSelectRequest={handleOpenDetailModal}
                onOpenReview={handleOpenReview}
                onOpenCorrection={handleOpenCorrection}
              />
            )}

            {activeTab === 'correction' && (
              <NeedsCorrectionTab
                onSelectRequest={handleOpenDetailModal}
                onOpenCorrection={handleOpenCorrection}
              />
            )}

            {activeTab === 'rejected' && (
              <RejectedRequestsTab onSelectRequest={handleOpenDetailModal} />
            )}

            {activeTab === 'customers' && (
              <CustomerRecordsTab onSelectRequest={handleOpenDetailModal} />
            )}

            {activeTab === 'agents' && <AgentMonitoringTab />}

            {activeTab === 'communication' && (
              <AgentCommunicationTab onSelectRequest={handleOpenDetailModal} />
            )}

            {activeTab === 'recovery' && <AgentRecoveryTab />}

            {activeTab === 'federation' && <BranchFederationTab />}

            {activeTab === 'admin' && <AdminManagementTab />}

            {activeTab === 'audit' && <AuditLogsTab />}
          </div>
        </main>
      </div>

      {/* Global Modals */}
      {inspectModalOpen && selectedRequest && (
        <RequestDetailModal
          request={selectedRequest}
          onClose={() => {
            setInspectModalOpen(false);
            setSelectedRequest(null);
          }}
          onOpenReview={(req) => {
            setInspectModalOpen(false);
            handleOpenReview(req);
          }}
          onOpenCorrection={(req) => {
            setInspectModalOpen(false);
            handleOpenCorrection(req);
          }}
          onInspectCustomer={(custId) => {
            setInspectModalOpen(false);
            setActiveTab('customers');
          }}
        />
      )}

      {reviewModalRequest && (
        <ReviewActionModal
          request={reviewModalRequest}
          onClose={() => setReviewModalRequest(null)}
          onSubmit={handleReviewSubmit}
        />
      )}

      {correctionModalRequest && (
        <CorrectionActionModal
          request={correctionModalRequest}
          onClose={() => setCorrectionModalRequest(null)}
          onSubmit={handleCorrectionSubmit}
        />
      )}
    </div>
  );
};
