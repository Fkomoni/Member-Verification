import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import { useAgentAuth } from "./context/AgentAuthContext";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import CallCenterLoginPage from "./pages/CallCenterLoginPage";
import CallCenterDashboardPage from "./pages/CallCenterDashboardPage";

function PrivateRoute({ children }) {
  const { provider } = useAuth();
  return provider ? children : <Navigate to="/login" replace />;
}

function AgentPrivateRoute({ children }) {
  const { agent } = useAgentAuth();
  return agent ? children : <Navigate to="/call-center/login" replace />;
}

export default function App() {
  return (
    <Routes>
      {/* Verification Portal */}
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/dashboard"
        element={
          <PrivateRoute>
            <DashboardPage />
          </PrivateRoute>
        }
      />

      {/* Call Center Portal */}
      <Route path="/call-center/login" element={<CallCenterLoginPage />} />
      <Route
        path="/call-center/dashboard"
        element={
          <AgentPrivateRoute>
            <CallCenterDashboardPage />
          </AgentPrivateRoute>
        }
      />

      {/* Default redirect */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
