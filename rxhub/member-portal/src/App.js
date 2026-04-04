import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Sidebar from './components/Sidebar';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import MedicationsPage from './pages/MedicationsPage';
import HealthReadingsPage from './pages/HealthReadingsPage';
import RequestsPage from './pages/RequestsPage';
import NewRequestPage from './pages/NewRequestPage';
import ResourcesPage from './pages/ResourcesPage';
import ProfilePage from './pages/ProfilePage';

function Protected({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div style={{ padding: 60, textAlign: 'center' }}>Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function Layout({ children }) {
  return (
    <div style={{ display: 'flex' }}>
      <Sidebar />
      <main style={{ flex: 1, marginLeft: 240, padding: '28px 32px', minHeight: '100vh', backgroundColor: '#F5F5F7' }}>
        {children}
      </main>
    </div>
  );
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<Protected><Layout><DashboardPage /></Layout></Protected>} />
      <Route path="/medications" element={<Protected><Layout><MedicationsPage /></Layout></Protected>} />
      <Route path="/health-readings" element={<Protected><Layout><HealthReadingsPage /></Layout></Protected>} />
      <Route path="/requests" element={<Protected><Layout><RequestsPage /></Layout></Protected>} />
      <Route path="/new-request" element={<Protected><Layout><NewRequestPage /></Layout></Protected>} />
      <Route path="/resources" element={<Protected><Layout><ResourcesPage /></Layout></Protected>} />
      <Route path="/profile" element={<Protected><Layout><ProfilePage /></Layout></Protected>} />
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
