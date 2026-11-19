import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { HomePage } from './pages/HomePage';
import { CustomerLoginPage } from './pages/customer/CustomerLoginPage';
import { CustomerRegisterPage } from './pages/customer/CustomerRegisterPage';
import { CustomerDashboardPage } from './pages/customer/CustomerDashboardPage';
import { BankLoginPage } from './pages/bank/BankLoginPage';
import { BankDashboardPage } from './pages/bank/BankDashboardPage';
import { ProtectedRoute } from './components/ProtectedRoute';

export const App = () => {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<HomePage />} />
      <Route path="/customer/login" element={<CustomerLoginPage />} />
      <Route path="/customer/register" element={<CustomerRegisterPage />} />
      <Route path="/bank/login" element={<BankLoginPage />} />

      {/* Protected Customer Routes */}
      <Route
        path="/customer/dashboard"
        element={
          <ProtectedRoute requiredRole="CUSTOMER">
            <CustomerDashboardPage />
          </ProtectedRoute>
        }
      />

      {/* Protected Bank Employee Routes */}
      <Route
        path="/bank/dashboard"
        element={
          <ProtectedRoute requiredRole="BANK_EMPLOYEE">
            <BankDashboardPage />
          </ProtectedRoute>
        }
      />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;
