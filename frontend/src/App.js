import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import LoginPage from "./pages/LoginPage";
import MedicationRequestPage from "./pages/MedicationRequestPage";
import RequestHistoryPage from "./pages/RequestHistoryPage";
import AdminReviewPage from "./pages/AdminReviewPage";
import ReportsPage from "./pages/ReportsPage";

function PrivateRoute({ children }) {
  const { provider } = useAuth();
  return provider ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/medication-request"
        element={<PrivateRoute><MedicationRequestPage /></PrivateRoute>}
      />
      <Route
        path="/medication-requests"
        element={<PrivateRoute><RequestHistoryPage /></PrivateRoute>}
      />
      <Route
        path="/admin/review"
        element={<PrivateRoute><AdminReviewPage /></PrivateRoute>}
      />
      <Route
        path="/reports"
        element={<PrivateRoute><ReportsPage /></PrivateRoute>}
      />
      {/* Default: redirect to medication request form */}
      <Route path="*" element={<Navigate to="/medication-request" replace />} />
    </Routes>
  );
}
