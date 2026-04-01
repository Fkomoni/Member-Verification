import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

export default function DashboardPage() {
  const [data, setData] = useState(null);
  const navigate = useNavigate();

  useEffect(() => { api.get('/member/dashboard').then(r => setData(r.data)).catch(() => {}); }, []);

  if (!data) return <p>Loading dashboard...</p>;
  const { profile, medications_count, pending_requests, unread_notifications, alerts } = data;

  return (
    <div>
      <div style={s.welcome}>
        <h1 style={s.heading}>Welcome back, {profile.first_name}</h1>
        <p style={s.sub}>ID: {profile.member_id} &middot; {profile.plan_name || profile.plan_type} &middot; {profile.diagnosis || 'No diagnosis on file'}</p>
      </div>

      <div style={s.stats}>
        <Stat label="Medications" value={medications_count} color="#1A1A2E" />
        <Stat label="Pending Requests" value={pending_requests} color="#E87722" />
        <Stat label="Unread Alerts" value={unread_notifications} color="#C8102E" />
      </div>

      {alerts.length > 0 && (
        <div style={{ marginTop: 28 }}>
          <h2 style={s.sectionTitle}>Refill Alerts</h2>
          {alerts.map((a, i) => (
            <div key={i} style={s.alert}>
              <strong>{a.medication}</strong> — {a.message}
              {a.days_remaining != null && <span style={s.days}>{a.days_remaining} days</span>}
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: 28 }}>
        <h2 style={s.sectionTitle}>Quick Actions</h2>
        <div style={s.actions}>
          <button style={{ ...s.actionBtn, backgroundColor: '#1A1A2E' }} onClick={() => navigate('/medications')}>View Medications</button>
          <button style={{ ...s.actionBtn, backgroundColor: '#C8102E' }} onClick={() => navigate('/new-request')}>New Request</button>
          <button style={{ ...s.actionBtn, backgroundColor: '#E87722' }} onClick={() => navigate('/health-readings')}>Log Health Reading</button>
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, color }) {
  return (
    <div style={s.statCard}>
      <div style={{ ...s.accent, backgroundColor: color }} />
      <div style={s.statVal}>{value}</div>
      <div style={s.statLabel}>{label}</div>
    </div>
  );
}

const s = {
  welcome: { marginBottom: 24 },
  heading: { fontSize: 26, fontWeight: 700, color: '#1A1A2E', margin: 0 },
  sub: { color: '#666', marginTop: 4, fontSize: 14 },
  stats: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 16 },
  statCard: { backgroundColor: '#fff', borderRadius: 12, padding: '20px 18px', position: 'relative', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.06)' },
  accent: { position: 'absolute', top: 0, left: 0, right: 0, height: 4 },
  statVal: { fontSize: 30, fontWeight: 700, color: '#1A1A2E' },
  statLabel: { fontSize: 13, color: '#666', marginTop: 2 },
  sectionTitle: { fontSize: 18, fontWeight: 700, color: '#1A1A2E', margin: '0 0 12px' },
  alert: { backgroundColor: '#FFF7ED', borderLeft: '4px solid #E87722', borderRadius: 8, padding: '12px 16px', marginBottom: 8, fontSize: 14, color: '#333' },
  days: { marginLeft: 8, color: '#E87722', fontWeight: 600, fontSize: 13 },
  actions: { display: 'flex', gap: 12 },
  actionBtn: { padding: '12px 24px', borderRadius: 8, border: 'none', color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer' },
};
