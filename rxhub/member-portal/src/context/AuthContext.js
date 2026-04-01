import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem('member_user');
    if (stored) setUser(JSON.parse(stored));
    setLoading(false);
  }, []);

  const login = async (memberId, phone) => {
    const { data } = await api.post('/auth/login', { member_id: memberId, phone });
    localStorage.setItem('member_token', data.access_token);
    const u = { memberId: data.member_id, name: data.member_name, authMethod: data.auth_method };
    localStorage.setItem('member_user', JSON.stringify(u));
    setUser(u);
    return data;
  };

  const sendOtp = async (memberId) => {
    const { data } = await api.post('/auth/send-otp', { member_id: memberId });
    return data;
  };

  const verifyOtp = async (memberId, otp) => {
    const { data } = await api.post('/auth/verify-otp', { member_id: memberId, otp });
    localStorage.setItem('member_token', data.access_token);
    const u = { memberId: data.member_id, name: data.member_name, authMethod: data.auth_method };
    localStorage.setItem('member_user', JSON.stringify(u));
    setUser(u);
    return data;
  };

  const logout = () => {
    localStorage.removeItem('member_token');
    localStorage.removeItem('member_user');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, sendOtp, verifyOtp, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
