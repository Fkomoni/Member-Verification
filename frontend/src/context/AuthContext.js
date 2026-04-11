import React, { createContext, useContext, useState, useCallback } from "react";
import { login as loginApi } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [provider, setProvider] = useState(() => {
    const stored = localStorage.getItem("provider");
    return stored ? JSON.parse(stored) : null;
  });

  const login = useCallback(async (email, password) => {
    const { data } = await loginApi(email, password);
    localStorage.setItem("access_token", data.access_token);
    const providerData = {
      provider_id: data.provider_id,
      provider_name: data.provider_name,
      prognosis_provider_id: data.prognosis_provider_id,
      role: data.role || "provider",
    };
    localStorage.setItem("provider", JSON.stringify(providerData));
    setProvider(providerData);
    return data;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("provider");
    setProvider(null);
  }, []);

  return (
    <AuthContext.Provider value={{ provider, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
