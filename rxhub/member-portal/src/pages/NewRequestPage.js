import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

export default function NewRequestPage() {
  const navigate = useNavigate();
  const [tab, setTab] = useState('profile');
  const [loading, setLoading] = useState(false);

  // Profile fields
  const [newPhone, setNewPhone] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newAddress, setNewAddress] = useState('');
  const [profileComment, setProfileComment] = useState('');

  // Medication fields
  const [medAction, setMedAction] = useState('ADD');
  const [drugName, setDrugName] = useState('');
  const [dosage, setDosage] = useState('');
  const [frequency, setFrequency] = useState('');
  const [medComment, setMedComment] = useState('');
  const [file, setFile] = useState(null);

  const submitProfile = async () => {
    if (!newPhone && !newEmail && !newAddress) return alert('Enter at least one field to update');
    setLoading(true);
    try {
      await api.post('/member/profile/update-request', { new_phone: newPhone || undefined, new_email: newEmail || undefined, new_address: newAddress || undefined, comment: profileComment || undefined });
      alert('Profile update request submitted!');
      navigate('/requests');
    } catch (err) { alert(err.response?.data?.detail || 'Failed'); }
    finally { setLoading(false); }
  };

  const submitMedication = async () => {
    if (!drugName) return alert('Drug name is required');
    if (medAction === 'ADD' && (!dosage || !frequency || !medComment)) return alert('All fields required for new medication');
    setLoading(true);
    try {
      const payload = medAction === 'ADD' ? { drug_name: drugName, dosage, frequency }
        : medAction === 'REMOVE' ? { drug_name: drugName }
        : { drug_name: drugName, new_dosage: dosage, new_frequency: frequency };

      const fd = new FormData();
      fd.append('request_type', 'MEDICATION_CHANGE');
      fd.append('action', medAction);
      fd.append('payload', JSON.stringify(payload));
      if (medComment) fd.append('comment', medComment);
      if (file) fd.append('attachment', file);

      await api.post('/requests', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      alert('Medication request submitted!');
      navigate('/requests');
    } catch (err) { alert(err.response?.data?.detail || 'Failed'); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <h1 style={s.heading}>New Request</h1>
      <p style={s.sub}>Submit a profile update or medication change request</p>

      <div style={s.tabs}>
        <button style={{ ...s.tab, ...(tab === 'profile' ? s.tabActive : {}) }} onClick={() => setTab('profile')}>Profile Update</button>
        <button style={{ ...s.tab, ...(tab === 'medication' ? s.tabActive : {}) }} onClick={() => setTab('medication')}>Medication Change</button>
      </div>

      {tab === 'profile' && (
        <div style={s.card}>
          <h2 style={s.cardTitle}>Update Your Profile</h2>
          <p style={s.cardSub}>Only fill fields you want to change. Changes go through approval.</p>

          <label style={s.label}>New Phone Number</label>
          <input style={s.input} value={newPhone} onChange={e => setNewPhone(e.target.value)} placeholder="e.g. 08098765432" />

          <label style={s.label}>New Email Address</label>
          <input style={s.input} value={newEmail} onChange={e => setNewEmail(e.target.value)} placeholder="e.g. new@email.com" />

          <label style={s.label}>New Address</label>
          <textarea style={{ ...s.input, minHeight: 60 }} value={newAddress} onChange={e => setNewAddress(e.target.value)} placeholder="Enter new address..." />

          <label style={s.label}>Reason (Optional)</label>
          <input style={s.input} value={profileComment} onChange={e => setProfileComment(e.target.value)} placeholder="e.g. Changed phone carrier" />

          <button style={s.btn} onClick={submitProfile} disabled={loading}>{loading ? 'Submitting...' : 'Submit Profile Update'}</button>
        </div>
      )}

      {tab === 'medication' && (
        <div style={s.card}>
          <h2 style={s.cardTitle}>Medication Change</h2>
          <div style={s.actionRow}>
            {['ADD', 'REMOVE', 'MODIFY'].map(a => (
              <button key={a} style={{ ...s.actionBtn, ...(medAction === a ? s.actionBtnActive : {}) }} onClick={() => setMedAction(a)}>{a}</button>
            ))}
          </div>

          <label style={s.label}>Medication Name</label>
          <input style={s.input} value={drugName} onChange={e => setDrugName(e.target.value)} placeholder="e.g. Amlodipine" />

          {(medAction === 'ADD' || medAction === 'MODIFY') && (
            <>
              <label style={s.label}>{medAction === 'MODIFY' ? 'New Dosage' : 'Dosage'}</label>
              <input style={s.input} value={dosage} onChange={e => setDosage(e.target.value)} placeholder="e.g. 500mg" />
              <label style={s.label}>{medAction === 'MODIFY' ? 'New Frequency' : 'Frequency'}</label>
              <input style={s.input} value={frequency} onChange={e => setFrequency(e.target.value)} placeholder="e.g. Twice daily" />
            </>
          )}

          <label style={s.label}>Comment / Reason</label>
          <textarea style={{ ...s.input, minHeight: 70 }} value={medComment} onChange={e => setMedComment(e.target.value)} placeholder="Reason for this change..." />

          {medAction === 'ADD' && (
            <>
              <label style={s.label}>Prescription Upload (Required for new meds)</label>
              <input type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={e => setFile(e.target.files[0])} style={{ fontSize: 13, marginBottom: 8 }} />
            </>
          )}

          <button style={s.btn} onClick={submitMedication} disabled={loading}>{loading ? 'Submitting...' : 'Submit Medication Request'}</button>
        </div>
      )}
    </div>
  );
}

const s = {
  heading: { fontSize: 26, fontWeight: 700, color: '#1A1A2E', margin: 0 },
  sub: { color: '#666', marginTop: 4, marginBottom: 20, fontSize: 14 },
  tabs: { display: 'flex', gap: 8, marginBottom: 20 },
  tab: { padding: '10px 20px', borderRadius: 8, border: '1px solid #ddd', backgroundColor: '#fff', cursor: 'pointer', fontSize: 14, fontWeight: 500 },
  tabActive: { backgroundColor: '#1A1A2E', color: '#fff', borderColor: '#1A1A2E' },
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 28, boxShadow: '0 1px 3px rgba(0,0,0,0.06)', display: 'flex', flexDirection: 'column', gap: 10, maxWidth: 560 },
  cardTitle: { fontSize: 18, fontWeight: 700, color: '#1A1A2E', margin: 0 },
  cardSub: { fontSize: 13, color: '#666', margin: '0 0 8px' },
  label: { fontSize: 12, fontWeight: 600, color: '#444', marginTop: 4 },
  input: { padding: '10px 12px', borderRadius: 8, border: '1px solid #ddd', fontSize: 14 },
  btn: { padding: '12px', borderRadius: 8, border: 'none', backgroundColor: '#C8102E', color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer', marginTop: 8 },
  actionRow: { display: 'flex', gap: 8, marginBottom: 8 },
  actionBtn: { padding: '8px 16px', borderRadius: 8, border: '1px solid #ddd', backgroundColor: '#fff', cursor: 'pointer', fontSize: 13, fontWeight: 500 },
  actionBtnActive: { backgroundColor: '#1A1A2E', color: '#fff', borderColor: '#1A1A2E' },
};
