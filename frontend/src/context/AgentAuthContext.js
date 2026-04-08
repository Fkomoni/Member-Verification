import React, { createContext, useContext, useState, useCallback } from "react";
import { agentLogin } from "../services/agentApi";

const AgentAuthContext = createContext(null);

export function AgentAuthProvider({ children }) {
  const [agent, setAgent] = useState(() => {
    const stored = localStorage.getItem("agent");
    return stored ? JSON.parse(stored) : null;
  });

  const login = useCallback(async (email, password) => {
    const { data } = await agentLogin(email, password);
    localStorage.setItem("agent_access_token", data.access_token);
    const agentData = {
      agent_id: data.agent_id,
      agent_name: data.agent_name,
      role: data.role,
    };
    localStorage.setItem("agent", JSON.stringify(agentData));
    setAgent(agentData);
    return data;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("agent_access_token");
    localStorage.removeItem("agent");
    setAgent(null);
  }, []);

  return (
    <AgentAuthContext.Provider value={{ agent, login, logout }}>
      {children}
    </AgentAuthContext.Provider>
  );
}

export function useAgentAuth() {
  const ctx = useContext(AgentAuthContext);
  if (!ctx) throw new Error("useAgentAuth must be used within AgentAuthProvider");
  return ctx;
}
