import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import RequestsPage from './pages/RequestsPage';
import RequestDetailPage from './pages/RequestDetailPage';
import AuditLogsPage from './pages/AuditLogsPage';
import ResourcesPage from './pages/ResourcesPage';
import Sidebar from './components/Sidebar';

function ProtectedRoute({ children }) {
  const { admin, loading } = useAuth();
  if (loading) return <div style={styles.loading}>Loading...</div>;
  if (!admin) return <Navigate to="/login" replace />;
  return children;
}

function AdminLayout({ children }) {
  return (
    <div style={styles.layout}>
      <Sidebar />
      <main style={styles.main}>{children}</main>
    </div>
  );
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<ProtectedRoute><AdminLayout><DashboardPage /></AdminLayout></ProtectedRoute>} />
      <Route path="/requests" element={<ProtectedRoute><AdminLayout><RequestsPage /></AdminLayout></ProtectedRoute>} />
      <Route path="/requests/:id" element={<ProtectedRoute><AdminLayout><RequestDetailPage /></AdminLayout></ProtectedRoute>} />
      <Route path="/audit-logs" element={<ProtectedRoute><AdminLayout><AuditLogsPage /></AdminLayout></ProtectedRoute>} />
      <Route path="/resources" element={<ProtectedRoute><AdminLayout><ResourcesPage /></AdminLayout></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}

const styles = {
  layout: { display: 'flex', minHeight: '100vh', fontFamily: "'Inter', sans-serif" },
  main: { flex: 1, padding: '32px', backgroundColor: '#F5F5F7', overflowY: 'auto' },
  loading: { display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', fontSize: 18, color: '#1A1A2E' },
};
