import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldAlert, ArrowLeft } from 'lucide-react';

export const ProtectedRoute = ({ children, requiredRole }) => {
  const { user, role, isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm text-slate-500 font-medium">Verifying authentication...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Redirect unauthenticated requests to appropriate login page based on role requirement
    const target = ['BANK_EMPLOYEE', 'SUPERVISOR', 'ADMINISTRATOR'].includes(requiredRole)
      ? '/bank/login'
      : '/customer/login';
    return <Navigate to={target} replace />;
  }

  const isAuthorized = () => {
    if (!requiredRole) return true;
    if (requiredRole === 'CUSTOMER') return role === 'CUSTOMER';
    if (requiredRole === 'BANK_EMPLOYEE') {
      return ['BANK_EMPLOYEE', 'SUPERVISOR', 'ADMINISTRATOR'].includes(role);
    }
    if (requiredRole === 'SUPERVISOR') {
      return ['SUPERVISOR', 'ADMINISTRATOR'].includes(role);
    }
    if (requiredRole === 'ADMINISTRATOR') {
      return role === 'ADMINISTRATOR';
    }
    return role === requiredRole;
  };

  if (!isAuthorized()) {
    const isStaffRole = ['BANK_EMPLOYEE', 'SUPERVISOR', 'ADMINISTRATOR'].includes(role);
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-100 p-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl border border-red-100 p-8 text-center space-y-4">
          <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto">
            <ShieldAlert className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">Access Restricted (403)</h2>
          <p className="text-sm text-slate-600 leading-relaxed">
            Your current account role <span className="font-semibold text-slate-800">({role})</span> does not have authorization to view this area.
            {requiredRole === 'CUSTOMER'
              ? ' This portal is reserved for registered retail customers.'
              : ' This portal is strictly reserved for authorized bank personnel.'}
          </p>
          <div className="pt-2">
            <a
              href={isStaffRole ? '/bank/dashboard' : '/customer/dashboard'}
              className="inline-flex items-center justify-center space-x-2 px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold rounded-xl transition"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Return to Your Dashboard</span>
            </a>
          </div>
        </div>
      </div>
    );
  }

  return children;
};
