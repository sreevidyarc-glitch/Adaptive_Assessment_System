import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi } from '../api/auth';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('adaptive_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('adaptive_token'));
  const [role, setRole] = useState(() => localStorage.getItem('adaptive_role'));
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('adaptive_token');
      if (storedToken) {
        try {
          const userData = await authApi.getMe();
          setUser(userData);
          setRole(userData.role);
          localStorage.setItem('adaptive_user', JSON.stringify(userData));
          localStorage.setItem('adaptive_role', userData.role);
        } catch (err) {
          console.error('Session expired or invalid:', err);
          logout();
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const setAuthSession = (tokenData) => {
    setToken(tokenData.access_token);
    setUser(tokenData.user);
    setRole(tokenData.role);
    localStorage.setItem('adaptive_token', tokenData.access_token);
    localStorage.setItem('adaptive_user', JSON.stringify(tokenData.user));
    localStorage.setItem('adaptive_role', tokenData.role);
  };

  const logout = async () => {
    await authApi.logout();
    setToken(null);
    setUser(null);
    setRole(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        role,
        isAuthenticated: !!token,
        isFaculty: role === 'FACULTY',
        isStudent: role === 'STUDENT',
        isLoading,
        setAuthSession,
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

