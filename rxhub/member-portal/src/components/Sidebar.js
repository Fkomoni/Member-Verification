import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const NAV = [
  { path: '/', label: 'Dashboard' },
  { path: '/medications', label: 'Medications' },
  { path: '/health-readings', label: 'Health Readings' },
  { path: '/requests', label: 'My Requests' },
  { path: '/new-request', label: 'New Request' },
  { path: '/resources', label: 'Resources' },
  { path: '/profile', label: 'Profile' },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <aside style={s.sidebar}>
      <div style={s.brand}>
        <img src="/leadway-logo.jpg" alt="Leadway Health" style={s.logo} />
      </div>
      <div style={s.appName}>
        <div style={s.title}>RxHub</div>
        <div style={s.sub}>Member Self-Service</div>
      </div>
      <nav style={s.nav}>
        {NAV.map(n => (
          <NavLink key={n.path} to={n.path} end={n.path === '/'} style={({ isActive }) => ({
            ...s.link, backgroundColor: isActive ? 'rgba(255,255,255,0.15)' : 'transparent',
            color: isActive ? '#fff' : 'rgba(255,255,255,0.65)',
          })}>{n.label}</NavLink>
        ))}
      </nav>
      <div style={s.footer}>
        <div style={s.userName}>{user?.name || 'Member'}</div>
        <div style={s.userId}>{user?.memberId}</div>
        <button onClick={() => { logout(); navigate('/login'); }} style={s.logoutBtn}>Sign Out</button>
      </div>
    </aside>
  );
}

const s = {
  sidebar: { width: 250, backgroundColor: '#262626', color: '#fff', display: 'flex', flexDirection: 'column', padding: '16px 0', minHeight: '100vh', position: 'fixed', left: 0, top: 0 },
  brand: { padding: '4px 20px 12px', textAlign: 'center' },
  logo: { width: 180, height: 'auto', objectFit: 'contain', borderRadius: 6 },
  appName: { padding: '0 20px 16px', borderBottom: '1px solid rgba(255,255,255,0.1)' },
  title: { fontWeight: 700, fontSize: 18, color: '#C8102E' },
  sub: { fontSize: 11, opacity: 0.5 },
  nav: { flex: 1, padding: '12px 8px', display: 'flex', flexDirection: 'column', gap: 2 },
  link: { display: 'block', padding: '10px 16px', borderRadius: 8, textDecoration: 'none', fontSize: 14, fontWeight: 500 },
  footer: { padding: '16px 20px', borderTop: '1px solid rgba(255,255,255,0.1)' },
  userName: { fontWeight: 600, fontSize: 13 },
  userId: { fontSize: 11, opacity: 0.5, marginBottom: 10 },
  logoutBtn: { background: 'none', border: '1px solid rgba(255,255,255,0.2)', color: '#fff', padding: '6px 14px', borderRadius: 6, cursor: 'pointer', fontSize: 12, width: '100%' },
};
