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
        <p style={s.sub}>ID: {profile.member_id} &middot; {profile.plan_name || profile.plan_type || 'N/A'} &middot; {profile.diagnosis || 'No diagnosis on file'}</p>
      </div>

      <div style={s.stats}>
        <Stat label="Medications" value={medications_count} color="#1A1A2E" />
        <Stat label="Pending Requests" value={pending_requests} color="#E87722" />
        <Stat label="Unread Alerts" value={unread_notifications} color="#C8102E" />
      </div>

      {alerts.length > 0 && (
        <div style={{ marginTop: 28 }}>
          <h2 style={s.sectionTitle}>Upcoming Refills</h2>
          {alerts.map((a, i) => (
            <div key={i} style={s.alert}>
              <div style={s.alertRow}>
                <strong>{a.medication}</strong>
                {a.next_refill_due && (
                  <span style={s.refillDate}>
                    Next refill: {new Date(a.next_refill_due).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
                  </span>
                )}
                {a.days_remaining != null && (
                  <span style={{
                    ...s.daysBadge,
                    backgroundColor: a.days_remaining <= 3 ? '#FEE2E2' : a.days_remaining <= 7 ? '#FFF7ED' : '#F0F4FF',
                    color: a.days_remaining <= 3 ? '#DC2626' : a.days_remaining <= 7 ? '#E87722' : '#2563EB',
                  }}>
                    {a.days_remaining <= 0 ? 'OVERDUE' : `${a.days_remaining} days left`}
                  </span>
                )}
              </div>
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
  alert: { backgroundColor: '#fff', borderLeft: '4px solid #E87722', borderRadius: 8, padding: '14px 18px', marginBottom: 8, boxShadow: '0 1px 2px rgba(0,0,0,0.04)' },
  alertRow: { display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' },
  refillDate: { fontSize: 13, color: '#1A1A2E', fontWeight: 600 },
  daysBadge: { padding: '3px 10px', borderRadius: 12, fontSize: 12, fontWeight: 700 },
  actions: { display: 'flex', gap: 12 },
  actionBtn: { padding: '12px 24px', borderRadius: 8, border: 'none', color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer' },
};
