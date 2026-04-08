import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import CallCenterLogin from "./pages/CallCenterLogin";
import CallCenterDashboard from "./pages/CallCenterDashboard";

function PrivateRoute({ children }) {
  const { provider } = useAuth();
  return provider ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      {/* Provider (biometric verification) routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/dashboard"
        element={
          <PrivateRoute>
            <DashboardPage />
          </PrivateRoute>
        }
      />

      {/* Call Center routes */}
      <Route path="/call-center/login" element={<CallCenterLogin />} />
      <Route path="/call-center/dashboard" element={<CallCenterDashboard />} />

      {/* Default: redirect to call center */}
      <Route path="*" element={<Navigate to="/call-center/dashboard" replace />} />
    </Routes>
  );
}
