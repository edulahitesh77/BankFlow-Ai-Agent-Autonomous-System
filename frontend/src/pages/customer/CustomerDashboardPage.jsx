import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  fetchCustomerDashboard,
  fetchCustomerAccounts,
  fetchCustomerProfile,
  fetchCustomerNotifications,
  markCustomerNotificationRead,
} from '../../api/auth';
import {
  ShieldCheck,
  LayoutDashboard,
  CreditCard,
  PlusCircle,
  FileText,
  Search,
  User,
  LogOut,
  Menu,
  X,
  Bell,
  Building,
} from 'lucide-react';
import { DashboardOverview } from './components/DashboardOverview';
import { AccountsTab } from './components/AccountsTab';
import { NewRequestTab } from './components/NewRequestTab';
import { MyRequestsTab } from './components/MyRequestsTab';
import { TrackRequestTab } from './components/TrackRequestTab';
import { ProfileTab } from './components/ProfileTab';

export const CustomerDashboardPage = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // Active tab state (synced with URL ?tab=...)
  const initialTab = searchParams.get('tab') || 'dashboard';
  const [activeTab, setActiveTab] = useState(initialTab);
  const [selectedRequestId, setSelectedRequestId] = useState(searchParams.get('requestId') || '');

  // Backend data state
  const [dashboardData, setDashboardData] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [profile, setProfile] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);
  const [loading, setLoading] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const loadData = async () => {
    try {
      const [dash, accs, prof, notifs] = await Promise.all([
        fetchCustomerDashboard(),
        fetchCustomerAccounts(),
        fetchCustomerProfile(),
        fetchCustomerNotifications().catch(() => ({ items: [], unread_count: 0 })),
      ]);
      setDashboardData(dash);
      setAccounts(accs);
      setProfile(prof);
      setNotifications(notifs.items || []);
      setUnreadCount(notifs.unread_count || 0);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleNotificationClick = async (notif) => {
    try {
      if (!notif.is_read) {
        await markCustomerNotificationRead(notif.id);
        setUnreadCount((prev) => Math.max(0, prev - 1));
        setNotifications((prev) =>
          prev.map((n) => (n.id === notif.id ? { ...n, is_read: true } : n))
        );
      }
      setShowNotifications(false);
      if (notif.request_id) {
        // Find request code or switch to tracking
        handleTabChange('my_requests');
      }
    } catch (e) {
      console.error('Error marking notification read:', e);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
    setSearchParams({ tab: tabId });
    setMobileMenuOpen(false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSelectRequestToTrack = (requestId) => {
    setSelectedRequestId(requestId);
    setActiveTab('track_request');
    setSearchParams({ tab: 'track_request', requestId });
  };

  const handleLogout = async () => {
    await logout();
    navigate('/customer/login');
  };

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'accounts', label: 'My Accounts', icon: CreditCard, count: accounts?.length },
    { id: 'new_request', label: 'New Service Request', icon: PlusCircle },
    { id: 'my_requests', label: 'My Requests', icon: FileText, count: dashboardData?.summary?.total_requests },
    { id: 'track_request', label: 'Track Request', icon: Search },
    { id: 'profile', label: 'My Profile', icon: User },
  ];

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm text-slate-500 font-medium">Loading BankFlow AI Customer Portal...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar for Desktop */}
      <aside className="hidden lg:flex lg:flex-col w-64 bg-white border-r border-slate-200/90 z-20 flex-shrink-0">
        {/* Brand Header */}
        <div className="h-20 flex items-center px-6 border-b border-slate-100">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center text-white shadow-md shadow-blue-500/20">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="text-lg font-bold text-slate-900 tracking-tight leading-tight">BankFlow</div>
              <div className="text-[11px] font-semibold text-blue-600 uppercase tracking-wider">Customer Portal</div>
            </div>
          </div>
        </div>

        {/* Customer Badge in Sidebar */}
        <div className="p-4 mx-4 mt-4 bg-slate-50 rounded-2xl border border-slate-100">
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Account Holder</div>
          <div className="text-sm font-bold text-slate-800 truncate">{dashboardData?.customer_name || user?.username}</div>
          <div className="text-xs font-mono font-medium text-blue-600 truncate">{dashboardData?.customer_code}</div>
        </div>

        {/* Navigation Menu */}
        <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleTabChange(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-3 rounded-2xl text-xs font-semibold transition ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.count !== undefined && item.count > 0 && (
                  <span
                    className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      isActive ? 'bg-white/20 text-white' : 'bg-slate-200/80 text-slate-700'
                    }`}
                  >
                    {item.count}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Sidebar Footer / Logout */}
        <div className="p-4 border-t border-slate-100">
          <button
            onClick={handleLogout}
            className="w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold text-slate-600 hover:text-rose-600 hover:bg-rose-50 transition"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Mobile Drawer Navigation */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div
            className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm"
            onClick={() => setMobileMenuOpen(false)}
          ></div>
          <div className="relative w-64 max-w-xs bg-white h-full flex flex-col z-10 shadow-2xl">
            <div className="h-16 flex items-center justify-between px-6 border-b border-slate-100">
              <div className="font-bold text-slate-900">Navigation Menu</div>
              <button onClick={() => setMobileMenuOpen(false)} className="p-1 text-slate-400 hover:text-slate-700">
                <X className="w-5 h-5" />
              </button>
            </div>
            <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
              {menuItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => handleTabChange(item.id)}
                    className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition ${
                      isActive ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <Icon className="w-4 h-4" />
                      <span>{item.label}</span>
                    </div>
                    {item.count !== undefined && item.count > 0 && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-200 text-slate-700">
                        {item.count}
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>
            <div className="p-4 border-t border-slate-100">
              <button
                onClick={handleLogout}
                className="w-full flex items-center space-x-2 px-3 py-2 text-xs font-semibold text-rose-600 hover:bg-rose-50 rounded-xl transition"
              >
                <LogOut className="w-4 h-4" />
                <span>Sign Out</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Navbar */}
        <header className="h-20 bg-white border-b border-slate-200/90 flex items-center justify-between px-4 sm:px-8 sticky top-0 z-10">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="lg:hidden p-2 text-slate-600 hover:bg-slate-100 rounded-xl"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div>
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Retail Banking</div>
              <div className="text-base sm:text-lg font-bold text-slate-900">
                {menuItems.find((m) => m.id === activeTab)?.label}
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-3 sm:space-x-4">
            <div className="hidden md:flex items-center space-x-2 px-3 py-1.5 bg-slate-100 rounded-xl text-xs text-slate-600">
              <Building className="w-3.5 h-3.5 text-slate-400" />
              <span>Branch: {dashboardData?.branch || 'Main Branch'}</span>
            </div>

            {/* Notifications Bell Dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-xl relative transition"
                title="Customer Notifications"
              >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                  <span className="absolute top-1.5 right-1.5 w-4 h-4 bg-orange-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center animate-pulse">
                    {unreadCount}
                  </span>
                )}
              </button>

              {showNotifications && (
                <div className="absolute right-0 mt-2 w-80 bg-white border border-slate-200 rounded-2xl shadow-2xl z-50 overflow-hidden text-xs">
                  <div className="p-3 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
                    <span className="font-bold text-slate-800">Notifications</span>
                    <span className="text-[11px] text-blue-600 font-semibold">{unreadCount} unread</span>
                  </div>
                  <div className="max-h-64 overflow-y-auto divide-y divide-slate-100">
                    {notifications.length > 0 ? (
                      notifications.map((n) => (
                        <div
                          key={n.id}
                          onClick={() => handleNotificationClick(n)}
                          className={`p-3.5 cursor-pointer transition hover:bg-slate-50 ${
                            !n.is_read ? 'bg-orange-50/50' : ''
                          }`}
                        >
                          <div className="font-bold text-slate-800 text-xs">{n.notification_title}</div>
                          <p className="text-slate-600 text-[11px] mt-0.5 line-clamp-2">{n.notification_message}</p>
                          <span className="text-[10px] text-slate-400 font-mono mt-1 block">
                            {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                      ))
                    ) : (
                      <div className="p-6 text-center text-slate-400">No notifications right now.</div>
                    )}
                  </div>
                </div>
              )}
            </div>

            <button
              onClick={() => handleTabChange('profile')}
              className="flex items-center space-x-2 p-1.5 sm:px-3 sm:py-1.5 rounded-xl hover:bg-slate-100 transition text-left"
            >
              <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-xs">
                {profile?.full_name?.charAt(0) || user?.username?.charAt(0) || 'U'}
              </div>
              <div className="hidden sm:block text-xs">
                <div className="font-bold text-slate-800 leading-tight">{profile?.full_name}</div>
                <div className="text-[10px] text-slate-400 font-mono">{profile?.customer_code}</div>
              </div>
            </button>

            <button
              onClick={handleLogout}
              className="hidden sm:inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:text-rose-600 hover:bg-rose-50 border border-slate-200 rounded-xl transition"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign Out</span>
            </button>
          </div>
        </header>

        {/* View Content Renderer */}
        <main className="flex-1 p-4 sm:p-8 max-w-7xl mx-auto w-full">
          {activeTab === 'dashboard' && (
            <DashboardOverview
              dashboardData={dashboardData}
              onNavigateTab={handleTabChange}
              onSelectRequest={handleSelectRequestToTrack}
            />
          )}

          {activeTab === 'accounts' && (
            <AccountsTab
              accounts={accounts}
              onRefreshAccounts={loadData}
            />
          )}

          {activeTab === 'new_request' && (
            <NewRequestTab
              accounts={accounts}
              onNavigateTab={handleTabChange}
              onSelectRequest={handleSelectRequestToTrack}
              onRefreshRequests={loadData}
            />
          )}

          {activeTab === 'my_requests' && (
            <MyRequestsTab
              onSelectRequest={handleSelectRequestToTrack}
              onNavigateTab={handleTabChange}
            />
          )}

          {activeTab === 'track_request' && (
            <TrackRequestTab
              selectedRequestId={selectedRequestId}
              onNavigateTab={handleTabChange}
            />
          )}

          {activeTab === 'profile' && (
            <ProfileTab
              profile={profile}
              onProfileUpdated={(updated) => setProfile(updated)}
            />
          )}
        </main>
      </div>
    </div>
  );
};
