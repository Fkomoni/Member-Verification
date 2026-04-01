import React, { createContext, useContext, useState, useEffect } from 'react';
import * as SecureStore from 'expo-secure-store';
import api from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const token = await SecureStore.getItemAsync('auth_token');
      const stored = await SecureStore.getItemAsync('user_data');
      if (token && stored) {
        setUser(JSON.parse(stored));
      }
      setLoading(false);
    })();
  }, []);

  const login = async (memberId, phone) => {
    const { data } = await api.post('/auth/login', { member_id: memberId, phone });
    await SecureStore.setItemAsync('auth_token', data.access_token);
    const userData = { memberId: data.member_id, name: data.member_name, authMethod: data.auth_method };
    await SecureStore.setItemAsync('user_data', JSON.stringify(userData));
    setUser(userData);
    return data;
  };

  const sendOtp = async (memberId) => {
    const { data } = await api.post('/auth/send-otp', { member_id: memberId });
    return data;
  };

  const verifyOtp = async (memberId, otp) => {
    const { data } = await api.post('/auth/verify-otp', { member_id: memberId, otp });
    await SecureStore.setItemAsync('auth_token', data.access_token);
    const userData = { memberId: data.member_id, name: data.member_name, authMethod: data.auth_method };
    await SecureStore.setItemAsync('user_data', JSON.stringify(userData));
    setUser(userData);
    return data;
  };

  const logout = async () => {
    await SecureStore.deleteItemAsync('auth_token');
    await SecureStore.deleteItemAsync('user_data');
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
