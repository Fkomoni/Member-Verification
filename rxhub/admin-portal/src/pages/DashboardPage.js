import React, { useState, useEffect } from 'react';
import api from '../services/api';

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/admin/analytics')
      .then(({ data }) => setStats(data))
      .catch(() => setStats(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading analytics...</p>;

  return (
    <div>
      <h1 style={styles.heading}>Dashboard</h1>
      <p style={styles.subtext}>LeadwayHMO RxHub — Admin Overview</p>

      <div style={styles.grid}>
        <StatCard label="Active Members" value={stats?.total_active_members ?? '-'} color="#1A1A2E" />
        <StatCard label="Active (30d)" value={stats?.members_with_activity_30d ?? '-'} color="#E87722" />
        <StatCard label="Pending Requests" value={stats?.request_stats?.pending ?? '-'} color="#C8102E" />
        <StatCard label="Approved" value={stats?.request_stats?.approved ?? '-'} color="#16A34A" />
        <StatCard label="Rejected" value={stats?.request_stats?.rejected ?? '-'} color="#DC2626" />
        <StatCard label="Modified" value={stats?.request_stats?.modified ?? '-'} color="#7C3AED" />
      </div>
    </div>
  );
}

function StatCard({ label, value, color }) {
  return (
    <div style={styles.card}>
      <div style={{ ...styles.cardAccent, backgroundColor: color }} />
      <div style={styles.cardValue}>{value}</div>
      <div style={styles.cardLabel}>{label}</div>
    </div>
  );
}

const styles = {
  heading: { fontSize: 28, fontWeight: 700, color: '#1A1A2E', margin: 0 },
  subtext: { color: '#666', marginTop: 4, marginBottom: 32 },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 20 },
  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: '24px 20px', position: 'relative',
    overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
  },
  cardAccent: { position: 'absolute', top: 0, left: 0, right: 0, height: 4 },
  cardValue: { fontSize: 32, fontWeight: 700, color: '#1A1A2E' },
  cardLabel: { fontSize: 13, color: '#666', marginTop: 4, fontWeight: 500 },
};
