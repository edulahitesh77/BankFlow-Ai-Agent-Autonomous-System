import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  getStoredToken,
  getStoredUser,
  storeSession,
  clearSession,
  fetchMe,
  logoutUser,
} from '../api/auth';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(getStoredToken());
  const [user, setUser] = useState(getStoredUser());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const verifySession = async () => {
      const storedTok = getStoredToken();
      if (!storedTok) {
        setLoading(false);
        return;
      }
      try {
        const me = await fetchMe();
        setUser(me);
        storeSession(storedTok, me);
      } catch {
        clearSession();
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    verifySession();

    const handleExpired = () => {
      clearSession();
      setToken(null);
      setUser(null);
    };
    window.addEventListener('bankflow:auth_expired', handleExpired);
    return () => window.removeEventListener('bankflow:auth_expired', handleExpired);
  }, []);

  const login = (accessToken, userData) => {
    setToken(accessToken);
    setUser(userData);
    storeSession(accessToken, userData);
  };

  const logout = async () => {
    try {
      await logoutUser();
    } finally {
      setToken(null);
      setUser(null);
      clearSession();
    }
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        role: user?.role || null,
        isAuthenticated: !!token && !!user,
        loading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
