import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const NAV_ITEMS = [
  { path: '/', label: 'Dashboard', icon: '\u25A0' },
  { path: '/requests', label: 'Requests', icon: '\u2709' },
  { path: '/audit-logs', label: 'Audit Logs', icon: '\u2630' },
  { path: '/resources', label: 'Resources', icon: '\u2605' },
];

export default function Sidebar() {
  const { admin, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <aside style={styles.sidebar}>
      <div style={styles.brand}>
        <div style={styles.logo}>Rx</div>
        <div>
          <div style={styles.title}>RxHub Admin</div>
          <div style={styles.subtitle}>LeadwayHMO</div>
        </div>
      </div>

      <nav style={styles.nav}>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            style={({ isActive }) => ({
              ...styles.navItem,
              backgroundColor: isActive ? 'rgba(255,255,255,0.15)' : 'transparent',
              color: isActive ? '#fff' : 'rgba(255,255,255,0.7)',
            })}
          >
            <span style={styles.icon}>{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div style={styles.footer}>
        <div style={styles.adminName}>{admin?.name || 'Admin'}</div>
        <div style={styles.adminRole}>{admin?.role || ''}</div>
        <button onClick={handleLogout} style={styles.logoutBtn}>Sign Out</button>
      </div>
    </aside>
  );
}

const styles = {
  sidebar: {
    width: 260, backgroundColor: '#1A1A2E', color: '#fff', display: 'flex',
    flexDirection: 'column', padding: '24px 0',
  },
  brand: { display: 'flex', alignItems: 'center', gap: 12, padding: '0 24px 24px', borderBottom: '1px solid rgba(255,255,255,0.1)' },
  logo: {
    width: 40, height: 40, borderRadius: 10, backgroundColor: '#C8102E', display: 'flex',
    alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 18,
  },
  title: { fontWeight: 700, fontSize: 16 },
  subtitle: { fontSize: 12, opacity: 0.6 },
  nav: { flex: 1, padding: '16px 12px', display: 'flex', flexDirection: 'column', gap: 4 },
  navItem: {
    display: 'flex', alignItems: 'center', gap: 12, padding: '10px 16px',
    borderRadius: 8, textDecoration: 'none', fontSize: 14, fontWeight: 500, transition: 'all 0.2s',
  },
  icon: { fontSize: 16, width: 20, textAlign: 'center' },
  footer: { padding: '16px 24px', borderTop: '1px solid rgba(255,255,255,0.1)' },
  adminName: { fontWeight: 600, fontSize: 14 },
  adminRole: { fontSize: 12, opacity: 0.6, marginBottom: 12 },
  logoutBtn: {
    background: 'none', border: '1px solid rgba(255,255,255,0.3)', color: '#fff',
    padding: '8px 16px', borderRadius: 6, cursor: 'pointer', fontSize: 13, width: '100%',
  },
};
