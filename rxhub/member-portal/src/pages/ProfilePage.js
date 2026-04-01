import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

export default function ProfilePage() {
  const [profile, setProfile] = useState(null);
  const { logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => { api.get('/member/profile').then(r => setProfile(r.data)).catch(() => {}); }, []);

  if (!profile) return <p>Loading...</p>;

  return (
    <div style={{ maxWidth: 560 }}>
      <h1 style={s.heading}>My Profile</h1>
      <p style={s.sub}>Your profile data is synced from the PBM system</p>

      <div style={s.card}>
        <div style={s.avatar}>{profile.first_name?.[0]}{profile.last_name?.[0]}</div>
        <h2 style={s.name}>{profile.first_name} {profile.last_name}</h2>
        <p style={s.memberId}>{profile.member_id}</p>

        <div style={s.fields}>
          <Field label="Email" value={profile.email || 'Not set'} />
          <Field label="Phone" value={profile.phone} />
          <Field label="Date of Birth" value={profile.date_of_birth || 'Not set'} />
          <Field label="Gender" value={profile.gender || 'Not set'} />
          <Field label="Diagnosis" value={profile.diagnosis || 'Not set'} />
          <Field label="Plan" value={`${profile.plan_name || ''} (${profile.plan_type || ''})`} />
          <Field label="Employer" value={profile.employer || 'Not set'} />
          <Field label="Status" value={profile.status} />
        </div>
      </div>

      <p style={s.note}>To update your phone, email, or address, go to <a href="/new-request" style={{ color: '#C8102E' }}>New Request</a> and submit a Profile Update.</p>

      <button onClick={() => { logout(); navigate('/login'); }} style={s.logoutBtn}>Sign Out</button>
    </div>
  );
}

function Field({ label, value }) {
  return (
    <div style={s.field}>
      <div style={{ fontSize: 12, color: '#999', fontWeight: 600 }}>{label}</div>
      <div style={{ fontSize: 14, color: '#1A1A2E', marginTop: 2 }}>{value}</div>
    </div>
  );
}

const s = {
  heading: { fontSize: 26, fontWeight: 700, color: '#1A1A2E', margin: 0 },
  sub: { color: '#666', marginTop: 4, marginBottom: 24, fontSize: 14 },
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 28, boxShadow: '0 1px 3px rgba(0,0,0,0.06)', textAlign: 'center' },
  avatar: { width: 64, height: 64, borderRadius: 32, backgroundColor: '#1A1A2E', color: '#fff', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, fontWeight: 700, marginBottom: 10 },
  name: { fontSize: 20, fontWeight: 700, color: '#1A1A2E', margin: 0 },
  memberId: { fontSize: 14, color: '#666', marginBottom: 20 },
  fields: { textAlign: 'left' },
  field: { padding: '12px 0', borderBottom: '1px solid #f0f0f0' },
  note: { fontSize: 13, color: '#666', marginTop: 16, lineHeight: 1.6 },
  logoutBtn: { marginTop: 24, padding: '12px 28px', borderRadius: 8, border: '1px solid #DC2626', backgroundColor: '#fff', color: '#DC2626', fontSize: 14, fontWeight: 600, cursor: 'pointer' },
};
