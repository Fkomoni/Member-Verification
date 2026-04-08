import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import { useAgentAuth } from "./context/AgentAuthContext";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import CallCenterLoginPage from "./pages/CallCenterLoginPage";
import CallCenterDashboardPage from "./pages/CallCenterDashboardPage";
import MemberPortalPage from "./pages/MemberPortalPage";
import ClaimsLoginPage from "./pages/ClaimsLoginPage";
import ClaimsPortalPage from "./pages/ClaimsPortalPage";

function PrivateRoute({ children }) {
  const { provider } = useAuth();
  return provider ? children : <Navigate to="/login" replace />;
}

function AgentPrivateRoute({ children, redirectTo }) {
  const { agent } = useAgentAuth();
  return agent ? children : <Navigate to={redirectTo || "/call-center/login"} replace />;
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

      {/* Member Portal (public) */}
      <Route path="/reimburse" element={<MemberPortalPage />} />

      {/* Claims Portal */}
      <Route path="/claims/login" element={<ClaimsLoginPage />} />
      <Route
        path="/claims/dashboard"
        element={
          <AgentPrivateRoute redirectTo="/claims/login">
            <ClaimsPortalPage />
          </AgentPrivateRoute>
        }
      />

      {/* Default redirect */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
